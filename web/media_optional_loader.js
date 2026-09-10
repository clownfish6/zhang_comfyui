import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const CONFIGS = {
    ImageOptionalLoader: {
        kind: "image",
        widgetName: "image",
        previewHeight: 220,
        accept: /\.(png|jpe?g|webp|gif|bmp|avif)$/i,
        label: "拖放图片到节点，自动加载",
        clearLabel: "清除图像",
    },
    AudioOptionalLoader: {
        kind: "audio",
        widgetName: "audio",
        previewHeight: 74,
        accept: /\.(mp3|wav|flac|ogg|m4a|aac|opus|mp4|mov|webm|mkv)$/i,
        label: "拖放音频到节点，自动加载",
        clearLabel: "清除音频",
    },
    VideoOptionalLoader: {
        kind: "video",
        widgetName: "file",
        previewHeight: 220,
        accept: /\.(mp4|webm|mov|avi|mkv|flv)$/i,
        label: "拖放视频到节点，自动加载",
        clearLabel: "清除视频",
    },
};

function firstFile(event, kind, accept) {
    return [...(event.dataTransfer?.files || [])].find(
        (file) => file.type?.startsWith(`${kind}/`) || accept.test(file.name || "")
    );
}

async function uploadFile(file) {
    const body = new FormData();
    body.append("image", file, file.name);
    body.append("type", "input");

    const response = await api.fetchApi("/upload/image", {
        method: "POST",
        body,
    });
    if (!response.ok) throw new Error(await response.text());

    const result = await response.json();
    if (!result?.name) throw new Error("Upload failed");
    return result.name;
}

function mediaUrl(filename) {
    return api.apiURL(
        `/view?filename=${encodeURIComponent(filename)}&type=input`
    );
}

function setWidgetFile(node, widgetName, filename) {
    const widget = node.widgets?.find((item) => item.name === widgetName);
    if (!widget) return;

    if (Array.isArray(widget.options?.values) && !widget.options.values.includes(filename)) {
        widget.options.values.push(filename);
    }
    widget.value = filename;
    widget.callback?.(filename);
}

app.registerExtension({
    name: "zhang.MediaOptionalLoader",

    setup() {
        const style = document.createElement("style");
        style.textContent = `
            .zhang-media-preview {
                position: relative;
                width: 100%;
                box-sizing: border-box;
                display: grid;
                place-items: center;
                overflow: hidden;
                border: 1px dashed var(--border-color, #666);
                border-radius: 8px;
                background: var(--comfy-input-bg, #222);
                color: var(--descrip-text, #aaa);
                font-size: 12px;
                text-align: center;
                transition: border-color .15s, background-color .15s;
            }
            .zhang-media-preview.dragover {
                border-color: #4f8cff;
                background: #1e2a44;
                color: #fff;
            }
            .zhang-media-preview img,
            .zhang-media-preview video {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }
            .zhang-media-preview audio {
                width: calc(100% - 16px);
            }
            .zhang-media-preview .zhang-preview-label {
                padding: 10px;
                pointer-events: none;
            }
        `;
        document.head.append(style);
    },

    beforeRegisterNodeDef(nodeType, nodeData) {
        const config = CONFIGS[nodeData.name];
        if (!config) return;

        const origOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const result = origOnNodeCreated?.apply(this, arguments);
            const node = this;
            const media = this.widgets?.find(
                (widget) => widget.name === config.widgetName
            );

            const container = document.createElement("div");
            container.className = "zhang-media-preview";
            container.style.height = `${config.previewHeight}px`;
            const preview = document.createElement(config.kind === "image" ? "img" : config.kind);
            if (config.kind !== "image") {
                preview.controls = true;
                preview.preload = "metadata";
            }
            preview.hidden = true;
            const label = document.createElement("div");
            label.className = "zhang-preview-label";
            label.textContent = config.label;
            container.append(preview, label);

            node._setPreview = function (url) {
                if (url) {
                    preview.src = url;
                    preview.hidden = false;
                    label.hidden = true;
                } else {
                    preview.pause?.();
                    preview.removeAttribute("src");
                    preview.load?.();
                    preview.hidden = true;
                    label.hidden = false;
                }
            };

            node._setPreviewFromSelected = function () {
                const filename = media?.value;
                node._setPreview(filename ? mediaUrl(filename) : "");
            };

            node._loadDroppedFile = async function (file) {
                const localUrl = URL.createObjectURL(file);
                node._setPreview(localUrl);

                try {
                    const filename = await uploadFile(file);
                    setWidgetFile(node, config.widgetName, filename);
                    node._setPreviewFromSelected();
                } catch (error) {
                    alert(`文件上传失败: ${error.message || error}`);
                    node._setPreviewFromSelected();
                } finally {
                    URL.revokeObjectURL(localUrl);
                }
            };

            node.onDragOver = function (event) {
                return Boolean(event.dataTransfer?.types?.includes("Files"));
            };

            node.onDragDrop = async function (event) {
                const file = firstFile(event, config.kind, config.accept);
                if (!file) return false;

                event.preventDefault();
                event.stopPropagation();
                await node._loadDroppedFile(file);
                node.setDirtyCanvas?.(true, true);
                return true;
            };

            container.addEventListener("dragover", (event) => {
                event.preventDefault();
                event.dataTransfer.dropEffect = "copy";
                container.classList.add("dragover");
            });
            container.addEventListener("dragleave", () => {
                container.classList.remove("dragover");
            });
            container.addEventListener("drop", (event) => {
                event.preventDefault();
                event.stopPropagation();
                container.classList.remove("dragover");
                node.onDragDrop(event);
            });

            if (media) {
                media.value = "";
                const originalCallback = media.callback;
                media.callback = function (...args) {
                    const callbackResult = originalCallback?.apply(this, args);
                    node._setPreviewFromSelected();
                    return callbackResult;
                };

                const clearButton = this.addWidget(
                    "button",
                    config.clearLabel,
                    null,
                    () => {
                        media.value = "";
                        node._setPreview("");
                        node.setDirtyCanvas?.(true, true);
                    }
                );
                clearButton.serialize = false;
                clearButton.options.serialize = false;
            }

            const previewWidget = this.addDOMWidget(
                `${config.kind}_preview`,
                "preview",
                container,
                { serialize: false, hideOnZoom: false }
            );
            previewWidget.computeSize = () => [
                node.size?.[0] || 240,
                config.previewHeight,
            ];
            previewWidget.serialize = false;

            this.setSize(this.computeSize());
            return result;
        };

        const origOnConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = origOnConfigure?.apply(this, arguments);
            this._setPreviewFromSelected?.();
            return result;
        };
    },
});
