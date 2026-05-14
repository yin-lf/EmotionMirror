class DynamicEmojiGenerator {
    constructor() {
        this.canvas = document.getElementById('previewCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.uploadedFiles = [];
        this.currentMediaIndex = 0;
        this.isPlaying = false;
        this.animationFrame = null;
        this.mediaElements = [];
        this.currentTime = 0;
        this.animationSpeed = 0.05;
        
        // 播放速度控制
        this.playbackSpeeds = [1, 1.5, 2, 3]; // 播放速度档位
        this.currentSpeedIndex = 0; // 当前速度索引
        this.switchInterval = 3000; // 基础媒体切换间隔(毫秒)
        
        // 文字动画相关
        this.textSettings = {
            text: '',
            x: 200,
            y: 200,
            fontSize: 24,
            color: '#ffffff',
            fontFamily: 'Arial, sans-serif',
            fontWeight: 'normal',
            animationType: 'none'
        };
        
        this.animationState = {
            time: 0,
            bounceOffset: 0,
            fadeOpacity: 1,
            rotateAngle: 0,
            shakeOffset: 0,
            typewriterIndex: 0
        };
        
        // 预览相关状态
        this.previewState = {
            isVisible: false,
            currentElement: null,
            currentFileObj: null,
            scrollThrottleTimer: null
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupCanvas();
        this.drawPlaceholder();
        this.updatePlayButton(); // 初始化按钮显示
        this.setupParentListener();
    }

    setupParentListener() {
        window.addEventListener('message', (e) => {
            if (e.data && e.data.type === 'initEmotion') {
                this.handleParentData(e.data);
            }
        });
    }

    async handleParentData(data) {
        // 设置文字
        if (data.emotion) {
            this.textSettings.text = data.emotion;
            const textInput = document.getElementById('textInput');
            if (textInput) textInput.value = data.emotion;
        }

        // 设置动画类型
        if (data.animationType) {
            this.textSettings.animationType = data.animationType;
            const animSelect = document.getElementById('animationType');
            if (animSelect) animSelect.value = data.animationType;
        }

        // 加载头像图片
        if (data.avatarUrl) {
            try {
                const resp = await fetch(data.avatarUrl);
                const blob = await resp.blob();
                const file = new File([blob], 'avatar.png', { type: blob.type || 'image/png' });
                this.addFile(file);
            } catch (err) {
                console.warn('从父窗口加载头像失败:', err);
            }
        }

        this.render();
    }
    
    setupEventListeners() {
        // 文件上传事件
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        // 拖拽事件 - 只处理拖拽，不处理点击
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        // 文件选择事件 - 使用原生label行为
        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            if (files.length > 0) {
                this.processFiles(files);
                // 重置文件输入框，允许再次选择相同文件
                e.target.value = '';
            }
        });
        
        // 播放控制
        document.getElementById('playBtn').addEventListener('click', () => {
            if (this.isPlaying) {
                // 如果正在播放，切换播放速度
                this.togglePlaybackSpeed();
            } else {
                // 如果未播放，开始播放
                this.play();
            }
        });
        document.getElementById('pauseBtn').addEventListener('click', () => this.pause());
        
        // 文字控制
        document.getElementById('textInput').addEventListener('input', () => this.updateTextSettings());
        document.getElementById('fontSize').addEventListener('input', () => this.updateTextSettings());
        document.getElementById('textColor').addEventListener('input', () => this.updateTextSettings());
        // 初始化自定义字体选择器
        this.initCustomFontSelector();
        document.getElementById('fontWeight').addEventListener('change', () => this.updateTextSettings());
        document.getElementById('animationType').addEventListener('change', () => this.updateTextSettings());
        document.getElementById('textX').addEventListener('input', () => this.updateTextSettings());
        document.getElementById('textY').addEventListener('input', () => this.updateTextSettings());
        
        // GIF设置
        document.getElementById('gifDuration').addEventListener('input', () => this.updateGifSettings());
        document.getElementById('gifQuality').addEventListener('input', () => this.updateGifSettings());
        
        // 操作按钮
        document.getElementById('generateBtn').addEventListener('click', () => this.generateGif());
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadGif());
        document.getElementById('resetBtn').addEventListener('click', () => this.reset());
        
        // 为文件列表添加拖拽排序事件
        this.setupDragAndDrop();
        
        // 添加滚动监听，优化预览框位置（带节流）
        this.scrollHandler = this.throttle(() => {
            this.updatePreviewPositionOnScroll();
        }, 16); // 约60fps更新频率
        
        window.addEventListener('scroll', this.scrollHandler, { passive: true });
    }
    
    setupDragAndDrop() {
        const fileList = document.getElementById('fileList');
        
        // 使用事件委托处理拖拽事件
        fileList.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('file-item')) {
                this.draggedIndex = Array.from(fileList.children).indexOf(e.target);
                e.target.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            }
        });
        
        fileList.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('file-item')) {
                e.target.classList.remove('dragging');
            }
        });
        
        fileList.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = this.getDragAfterElement(fileList, e.clientY);
            const dragging = fileList.querySelector('.dragging');
            
            if (afterElement == null) {
                fileList.appendChild(dragging);
            } else {
                fileList.insertBefore(dragging, afterElement);
            }
        });
        
        fileList.addEventListener('drop', (e) => {
            e.preventDefault();
            this.updateFileOrder();
        });
    }
    
    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.file-item:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
    
    updateFileOrder() {
        const fileList = document.getElementById('fileList');
        const items = Array.from(fileList.children);
        
        // 根据新的DOM顺序重新排序uploadedFiles数组
        const newOrder = [];
        items.forEach(item => {
            const index = parseInt(item.dataset.index);
            if (!isNaN(index) && this.uploadedFiles[index]) {
                newOrder.push(this.uploadedFiles[index]);
            }
        });
        
        this.uploadedFiles = newOrder;
        
        // 重新渲染文件列表
        this.updateFileList();
        
        // 如果正在播放，更新当前媒体索引
        if (this.isPlaying) {
            this.currentMediaIndex = Math.max(0, Math.min(this.currentMediaIndex, this.uploadedFiles.length - 1));
        }
    }
    
    // 移除单独的handleFileSelect方法，直接在setupEventListeners中处理
    
    setupCanvas() {
        this.canvas.width = 300;
        this.canvas.height = 300;
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, 300, 300);
    }
    
    drawPlaceholder() {
        this.ctx.fillStyle = '#f8f9fa';
        this.ctx.fillRect(0, 0, 300, 300);
        
        this.ctx.fillStyle = '#ccc';
        this.ctx.font = '20px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.fillText('上传图片或视频开始创作', 150, 150);
    }
    
    // 拖拽处理
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        this.processFiles(files);
    }
    
    processFiles(files) {
        const validFiles = files.filter(file => {
            const isImage = file.type.startsWith('image/');
            const isVideo = file.type.startsWith('video/');
            return isImage || isVideo;
        });
        
        if (validFiles.length === 0) {
            alert('请选择有效的图片或视频文件');
            return;
        }
        
        // 大量文件提示
        if (validFiles.length > 50) {
            if (!confirm(`⚠️ 您选择了 ${validFiles.length} 个文件，这可能会影响性能。是否继续？`)) {
                return;
            }
        }
        
        // 记录处理前是否已有文件
        const hadFilesBeforeProcessing = this.uploadedFiles.length > 0;
        
        // 按文件名排序后添加
        const sortedFiles = validFiles.sort((a, b) => a.name.localeCompare(b.name));
        sortedFiles.forEach(file => this.addFile(file));
        
        // 如果之前没有文件，现在有了文件，确保自动播放
        if (!hadFilesBeforeProcessing && this.uploadedFiles.length > 0) {
            // 延时确保文件元素已创建
            setTimeout(() => {
                if (!this.isPlaying && this.uploadedFiles.length > 0) {
                    this.play();
                }
            }, 100);
        }
    }
    
    addFile(file) {
        const fileObj = {
            file: file,
            name: file.name,
            size: this.formatFileSize(file.size),
            type: file.type.startsWith('image/') ? 'image' : 'video',
            url: URL.createObjectURL(file),
            element: null
        };
        
        this.uploadedFiles.push(fileObj);
        
        // 立即更新文件列表，显示加载状态
        this.updateFileList();
        
        // 创建媒体元素并等待加载
        this.createMediaElement(fileObj).then(() => {
            if (this.uploadedFiles.length === 1) {
                this.currentMediaIndex = Math.max(0, this.uploadedFiles.length - 1);
                this.play();
            } else {
                this.render();
            }
        });
    }
    
    createMediaElement(fileObj) {
        return new Promise((resolve) => {
            if (fileObj.type === 'image') {
                const img = new Image();
                
                img.onload = () => {
                    fileObj.element = img;
                    
                    // 对于抽取帧，额外设置图片尺寸信息
                    if (fileObj.isExtractedFrame) {
                        fileObj.naturalWidth = img.naturalWidth;
                        fileObj.naturalHeight = img.naturalHeight;
                        fileObj.ready = true; // 标记为已就绪
                        console.log(`抽取帧加载成功: ${fileObj.name} (${img.naturalWidth}x${img.naturalHeight})`);
                    }
                    
                    this.updateFileList(); // 更新显示
                    resolve();
                };
                
                img.onerror = (error) => {
                    console.error('图片加载失败:', fileObj.name, error);
                    fileObj.error = '加载失败';
                    this.updateFileList();
                    resolve();
                };
                
                // 对于抽取帧（DataURL），不需要跨域设置
                if (!fileObj.isExtractedFrame) {
                    img.crossOrigin = 'anonymous';
                }
                
                // 使用DataURL或文件URL
                img.src = fileObj.dataURL || fileObj.url;
            } else {
                const video = document.createElement('video');
                video.muted = true;
                video.loop = true;
                video.preload = 'metadata'; // 预加载元数据
                
                // 增强视频元数据处理
                video.onloadedmetadata = () => {
                    // 存储视频元数据
                    fileObj.duration = video.duration;
                    fileObj.videoWidth = video.videoWidth;
                    fileObj.videoHeight = video.videoHeight;
                    fileObj.element = video;
                    this.updateFileList();
                };
                
                video.onloadeddata = () => {
                    // 视频数据加载完成，可以进行抽帧操作
                    fileObj.readyForExtraction = true;
                    this.updateFileList();
                    resolve();
                };
                
                video.onerror = () => {
                    console.error('视频加载失败:', fileObj.name);
                    fileObj.error = '加载失败';
                    this.updateFileList();
                    resolve();
                };
                
                // 监听视频可以播放事件
                video.oncanplay = () => {
                    fileObj.canPlay = true;
                };
                
                video.src = fileObj.url;
            }
        });
    }
    
    updateFileList() {
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';
        
        // 添加文件计数和排序提示
        if (this.uploadedFiles.length > 0) {
            const countItem = document.createElement('div');
            countItem.style.cssText = 'background: #e3f2fd; padding: 10px; border-radius: 8px; margin-bottom: 2px; text-align: center; font-weight: bold; color: #1976d2;';
            countItem.innerHTML = `📊 已上传 ${this.uploadedFiles.length} 个文件 | 已按文件名排序 | 可拖拽调整顺序`;
            fileList.appendChild(countItem);
        }
        
        this.uploadedFiles.forEach((fileObj, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.draggable = true;
            fileItem.dataset.index = index;
            
            let previewContent, statusText, extractBtn = '';
            
            if (fileObj.error) {
                previewContent = '❌';
                statusText = fileObj.error;
            } else if (!fileObj.element) {
                previewContent = '<div class="loading-spinner">⏳</div>';
                statusText = '加载中...';
            } else {
                if (fileObj.type === 'image') {
                    previewContent = fileObj.isExtractedFrame ? '🎬→🖼️' : '🖼️';
                    // 如果是抽取帧，显示额外信息
                    if (fileObj.isExtractedFrame) {
                        statusText = `抽取帧 (${fileObj.frameTime?.toFixed(1)}s)`;
                        if (!fileObj.ready && !fileObj.error) {
                            statusText += ' - 加载中...';
                        } else if (fileObj.ready) {
                            statusText += ' - 就绪';
                        }
                    }
                } else {
                    previewContent = '🎬';
                    // 为视频添加抽帧按钮，只有在视频数据准备好时才启用
                    const isDisabled = !fileObj.readyForExtraction ? 'disabled' : '';
                    const buttonTitle = fileObj.readyForExtraction ? '视频抽帧' : '视频加载中...';
                    extractBtn = `<button class="file-extract-btn" ${isDisabled} onclick="generator.showFrameExtractionModal(${index})" title="${buttonTitle}">抽帧</button>`;
                    
                    // 显示视频详细信息
                    if (fileObj.duration && fileObj.videoWidth && fileObj.videoHeight) {
                        statusText = `${fileObj.duration.toFixed(1)}s - ${fileObj.videoWidth}x${fileObj.videoHeight}`;
                    }
                }
            }
            
            fileItem.innerHTML = `
                <div class="file-drag-handle" title="拖拽调整顺序">⋮⋮</div>
                <div class="file-preview" style="background: #ddd; display: flex; align-items: center; justify-content: center; color: #666;">
                    ${previewContent}
                </div>
                <div class="file-info">
                    <div class="file-name" data-file-index="${index}">${index + 1}. ${fileObj.name}</div>
                    <div class="file-size">${fileObj.size}</div>
                    ${statusText ? `<div class="file-status">${statusText}</div>` : ''}
                </div>
                <div class="file-actions">
                    ${extractBtn}
                    <button class="file-remove" onclick="generator.removeFile(${index})">删除</button>
                </div>
            `;
            fileList.appendChild(fileItem);
        });
        
        // 为文件名添加预览事件监听器
        this.setupFilePreviewListeners();
    }
    
    removeFile(index) {
        URL.revokeObjectURL(this.uploadedFiles[index].url);
        this.uploadedFiles.splice(index, 1);
        
        if (this.currentMediaIndex >= this.uploadedFiles.length) {
            this.currentMediaIndex = Math.max(0, this.uploadedFiles.length - 1);
        }
        
        this.updateFileList();
        
        if (this.uploadedFiles.length === 0) {
            this.pause();
            this.drawPlaceholder();
        } else {
            this.render();
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // 切换播放速度
    togglePlaybackSpeed() {
        this.currentSpeedIndex = (this.currentSpeedIndex + 1) % this.playbackSpeeds.length;
        this.updatePlayButton();
        console.log(`播放速度切换为: ${this.getCurrentPlaybackSpeed()}x`);
    }
    
    // 获取当前播放速度
    getCurrentPlaybackSpeed() {
        return this.playbackSpeeds[this.currentSpeedIndex];
    }
    
    // 更新播放按钮显示
    updatePlayButton() {
        this.updatePlayButtonStates();
    }
    
    // 同步播放和暂停按钮状态
    updatePlayButtonStates() {
        const playBtn = document.getElementById('playBtn');
        const pauseBtn = document.getElementById('pauseBtn');
        const speed = this.getCurrentPlaybackSpeed();
        
        if (this.isPlaying) {
            playBtn.innerHTML = `▶️ 播放 ${speed}x`;
            playBtn.disabled = false; // 播放时可以切换速度
            pauseBtn.disabled = false;
        } else {
            playBtn.innerHTML = `▶️ 播放 ${speed}x`;
            playBtn.disabled = false;
            pauseBtn.disabled = true; // 暂停时禁用暂停按钮
        }
        
        // 如果没有文件，禁用所有按钮
        const hasFiles = this.uploadedFiles.length > 0;
        if (!hasFiles) {
            playBtn.disabled = true;
            pauseBtn.disabled = true;
        }
    }

    play() {
        if (this.uploadedFiles.length === 0) return;
        
        // 检查文件有效性
        const validFiles = this.getValidFiles();
        if (validFiles.length === 0) {
            console.warn('没有有效的文件可以播放');
            return;
        }
        
        // 确保当前索引有效
        this.ensureValidCurrentIndex();
        
        this.isPlaying = true;
        this.updatePlayButton(); // 更新按钮显示
        
        // 统一播放逻辑：支持视频+图片混合播放
        this.startPlayback();
        this.animate();
    }
    
    // 获取所有有效的文件（已加载且有element的文件）
    getValidFiles() {
        return this.uploadedFiles.filter(file => 
            file && file.element && !file.error
        );
    }
    
    // 确保当前媒体索引指向有效文件
    ensureValidCurrentIndex() {
        const validFiles = this.getValidFiles();
        if (validFiles.length === 0) return;
        
        // 如果当前索引无效，找到第一个有效文件
        const currentFile = this.uploadedFiles[this.currentMediaIndex];
        if (!currentFile || !currentFile.element || currentFile.error) {
            // 找到第一个有效文件的索引
            for (let i = 0; i < this.uploadedFiles.length; i++) {
                const file = this.uploadedFiles[i];
                if (file && file.element && !file.error) {
                    this.currentMediaIndex = i;
                    console.log(`切换到有效文件: ${file.name} (索引: ${i})`);
                    break;
                }
            }
        }
    }
    
    // 启动播放的统一处理
    startPlayback() {
        const currentFile = this.uploadedFiles[this.currentMediaIndex];
        if (!currentFile || !currentFile.element) return;
        
        // 如果是视频，启动视频播放
        if (currentFile.type === 'video') {
            currentFile.element.play().catch(err => {
                console.warn('视频播放失败:', err);
            });
        }
        // 图片和抽取帧不需要特殊处理，通过animate方法统一管理
        
        console.log(`开始播放: ${currentFile.name} (${currentFile.type})`);
    }
    
    pause() {
        this.isPlaying = false;
        this.updatePlayButton(); // 更新按钮显示
        
        // 暂停所有视频
        this.uploadedFiles.forEach(fileObj => {
            if (fileObj.type === 'video' && fileObj.element) {
                fileObj.element.pause();
            }
        });
        
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        
        console.log('播放已暂停');
    }
    
    animate() {
        if (!this.isPlaying) return;
        
        const speedMultiplier = this.getCurrentPlaybackSpeed();
        this.currentTime += this.animationSpeed * speedMultiplier;
        this.animationState.time = this.currentTime;
        
        // 智能媒体切换逻辑
        if (this.uploadedFiles.length > 1) {
            const oldIndex = this.currentMediaIndex;
            this.updateCurrentMediaIndex();
            
            // 如果切换到新文件，处理播放状态
            if (oldIndex !== this.currentMediaIndex) {
                this.handleMediaSwitch(oldIndex, this.currentMediaIndex);
            }
        }
        
        this.render();
        this.animationFrame = requestAnimationFrame(() => this.animate());
    }
    
    // 更新当前媒体索引
    updateCurrentMediaIndex() {
        const validFiles = this.getValidFiles();
        if (validFiles.length === 0) return;
        
        const switchInterval = this.getSwitchInterval();
        
        // 计算基于有效文件的索引
        const validIndex = Math.floor(this.currentTime / switchInterval) % validFiles.length;
        
        // 找到有效文件在uploadedFiles中的实际索引
        let count = 0;
        for (let i = 0; i < this.uploadedFiles.length; i++) {
            const file = this.uploadedFiles[i];
            if (file && file.element && !file.error) {
                if (count === validIndex) {
                    this.currentMediaIndex = i;
                    break;
                }
                count++;
            }
        }
    }
    
    // 获取切换间隔（根据文件类型和播放速度动态调整）
    getSwitchInterval() {
        const currentFile = this.uploadedFiles[this.currentMediaIndex];
        const speedMultiplier = this.getCurrentPlaybackSpeed();
        
        let baseInterval;
        // 对于视频，使用固定的3秒间隔
        if (currentFile && currentFile.type === 'video') {
            baseInterval = 3;
        } else {
            // 对于图片和抽取帧，使用较短的间隔以更好的动画效果
            baseInterval = 2;
        }
        
        // 根据播放速度调整间隔（速度越快，间隔越短）
        return baseInterval / speedMultiplier;
    }
    
    // 处理媒体切换
    handleMediaSwitch(oldIndex, newIndex) {
        const oldFile = this.uploadedFiles[oldIndex];
        const newFile = this.uploadedFiles[newIndex];
        
        if (!newFile || !newFile.element) return;
        
        // 暂停之前的视频
        if (oldFile && oldFile.type === 'video' && oldFile.element) {
            oldFile.element.pause();
        }
        
        // 启动新的媒体
        if (newFile.type === 'video') {
            newFile.element.play().catch(err => {
                console.warn('视频切换播放失败:', err);
            });
        }
        
        console.log(`媒体切换: ${oldFile?.name || '未知'} → ${newFile.name} (${newFile.type})`);
    }
    
    render() {
        // 清空画布
        this.ctx.clearRect(0, 0, 300, 300);
        
        // 绘制背景
        this.drawBackground();
        
        // 绘制文字
        this.drawText();
    }
    
    drawBackground() {
        const currentFile = this.uploadedFiles[this.currentMediaIndex];
        if (!currentFile || !currentFile.element) {
            this.ctx.fillStyle = '#f8f9fa';
            this.ctx.fillRect(0, 0, 300, 300);
            return;
        }
        
        const element = currentFile.element;
        
        // 计算缩放比例以适应1:1比例
        let sourceWidth, sourceHeight;
        
        if (currentFile.type === 'image') {
            sourceWidth = element.naturalWidth;
            sourceHeight = element.naturalHeight;
        } else {
            sourceWidth = element.videoWidth;
            sourceHeight = element.videoHeight;
        }
        
        if (sourceWidth === 0 || sourceHeight === 0) return;
        
        // 计算居中裁剪
        const scale = Math.max(300 / sourceWidth, 300 / sourceHeight);
        const scaledWidth = sourceWidth * scale;
        const scaledHeight = sourceHeight * scale;
        const x = (300 - scaledWidth) / 2;
        const y = (300 - scaledHeight) / 2;
        
        this.ctx.drawImage(element, x, y, scaledWidth, scaledHeight);
    }
    
    drawText() {
        if (!this.textSettings.text) return;
        
        this.ctx.save();
        
        // 设置字体样式
        this.ctx.font = `${this.textSettings.fontWeight} ${this.textSettings.fontSize}px ${this.textSettings.fontFamily}`;
        this.ctx.fillStyle = this.textSettings.color;
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 2;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        // 应用动画效果
        this.applyTextAnimation();
        
        // 绘制文字描边和填充
        this.ctx.strokeText(this.getDisplayText(), this.textSettings.x, this.textSettings.y);
        this.ctx.fillText(this.getDisplayText(), this.textSettings.x, this.textSettings.y);
        
        this.ctx.restore();
    }
    
    applyTextAnimation() {
        const time = this.animationState.time;
        const speedMultiplier = this.getCurrentPlaybackSpeed();
        
        switch (this.textSettings.animationType) {
            case 'bounce':
                this.animationState.bounceOffset = Math.sin(time * 4 * speedMultiplier) * 10;
                this.ctx.translate(0, this.animationState.bounceOffset);
                break;
                
            case 'fade':
                this.animationState.fadeOpacity = (Math.sin(time * 3 * speedMultiplier) + 1) / 2;
                this.ctx.globalAlpha = this.animationState.fadeOpacity;
                break;
                
            case 'rotate':
                this.animationState.rotateAngle = time * 2 * speedMultiplier;
                const scale = 0.8 + Math.sin(time * 2 * speedMultiplier) * 0.2;
                this.ctx.translate(this.textSettings.x, this.textSettings.y);
                this.ctx.rotate(this.animationState.rotateAngle);
                this.ctx.scale(scale, scale);
                this.ctx.translate(-this.textSettings.x, -this.textSettings.y);
                break;
                
            case 'shake':
                this.animationState.shakeOffset = Math.sin(time * 8 * speedMultiplier) * 5;
                this.ctx.translate(this.animationState.shakeOffset, 0);
                break;
                
            case 'typewriter':
                this.animationState.typewriterIndex = Math.floor(time * 3 * speedMultiplier) % (this.textSettings.text.length + 10);
                break;
                
            // 新增高级动画效果
            case 'slide':
                const slideProgress = (Math.sin(time * 2 * speedMultiplier) + 1) / 2;
                this.ctx.translate((slideProgress - 0.5) * 100, 0);
                break;
                
            case 'zoom':
                const zoomScale = 0.8 + Math.sin(time * 4 * speedMultiplier) * 0.4;
                this.ctx.translate(this.textSettings.x, this.textSettings.y);
                this.ctx.scale(zoomScale, zoomScale);
                this.ctx.translate(-this.textSettings.x, -this.textSettings.y);
                break;
                
            case 'rainbow':
                const hue = (time * 60 * speedMultiplier) % 360;
                this.ctx.fillStyle = `hsl(${hue}, 80%, 60%)`;
                break;
                
            case 'wave':
                const waveOffset = Math.sin(time * 3 * speedMultiplier) * 15;
                this.ctx.translate(0, waveOffset);
                // 添加波浪形状的字符偏移
                const chars = this.getDisplayText().split('');
                if (chars.length > 1) {
                    this.ctx.translate(Math.sin(time * 5 * speedMultiplier) * 3, 0);
                }
                break;
                
            case 'flip':
                const flipAngle = Math.sin(time * 2 * speedMultiplier) * Math.PI;
                this.ctx.translate(this.textSettings.x, this.textSettings.y);
                this.ctx.scale(Math.cos(flipAngle), 1);
                this.ctx.translate(-this.textSettings.x, -this.textSettings.y);
                break;
                
            case 'elastic':
                const elasticX = 1 + Math.sin(time * 4 * speedMultiplier) * 0.3;
                const elasticY = 1 + Math.cos(time * 4 * speedMultiplier) * 0.2;
                this.ctx.translate(this.textSettings.x, this.textSettings.y);
                this.ctx.scale(elasticX, elasticY);
                this.ctx.translate(-this.textSettings.x, -this.textSettings.y);
                break;
                
            case 'glitch':
                if (Math.random() < 0.1) { // 10% 概率触发故障效果
                    this.ctx.translate((Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10);
                    const glitchColors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'];
                    this.ctx.fillStyle = glitchColors[Math.floor(Math.random() * glitchColors.length)];
                }
                break;
                
            case 'orbit':
                const orbitRadius = 20;
                const orbitX = Math.cos(time * 3 * speedMultiplier) * orbitRadius;
                const orbitY = Math.sin(time * 3 * speedMultiplier) * orbitRadius;
                this.ctx.translate(orbitX, orbitY);
                this.ctx.rotate(time * 2 * speedMultiplier);
                break;
        }
    }
    
    getDisplayText() {
        if (this.textSettings.animationType === 'typewriter') {
            const index = Math.min(this.animationState.typewriterIndex, this.textSettings.text.length);
            return this.textSettings.text.substring(0, index);
        }
        return this.textSettings.text;
    }
    
    updateTextSettings() {
        this.textSettings.text = document.getElementById('textInput').value;
        this.textSettings.fontSize = parseInt(document.getElementById('fontSize').value);
        this.textSettings.color = document.getElementById('textColor').value;
        // 字体家族从自定义选择器获取，如果还在使用旧的select则保持兼容
        if (this.selectedFontFamily) {
            this.textSettings.fontFamily = this.selectedFontFamily;
        } else {
            const fontFamilyElement = document.getElementById('fontFamily');
            if (fontFamilyElement) {
                this.textSettings.fontFamily = fontFamilyElement.value;
            }
        }
        this.textSettings.fontWeight = document.getElementById('fontWeight').value;
        this.textSettings.animationType = document.getElementById('animationType').value;
        this.textSettings.x = parseInt(document.getElementById('textX').value);
        this.textSettings.y = parseInt(document.getElementById('textY').value);
        
        // 更新显示值
        document.getElementById('fontSizeValue').textContent = this.textSettings.fontSize + 'px';
        
        this.render();
    }
    
    // 指定质量生成GIF的辅助方法
    async generateWithQuality(quality) {
        return new Promise((resolve, reject) => {
            const duration = parseInt(document.getElementById('gifDuration').value);
            const fps = 10;
            const totalFrames = duration * fps;
            
            // 创建GIF
            const gif = new GIF({
                workers: 2,
                quality: quality,
                width: 300,
                height: 300,
                workerScript: 'js/gif.worker.js'
            });
            
            // 生成帧的异步函数
            const generateFrames = async () => {
                for (let i = 0; i < totalFrames; i++) {
                    // 更新动画时间
                    this.currentTime = (i / fps);
                    this.animationState.time = this.currentTime;
                    
                    // 更新媒体索引
                    if (this.uploadedFiles.length > 1) {
                        this.updateCurrentMediaIndex();
                    }
                    
                    // 渲染当前帧
                    this.render();
                    
                    // 添加到GIF
                    gif.addFrame(this.canvas, { delay: 100 });
                    
                    // 让浏览器有时间更新UI
                    await new Promise(resolve => setTimeout(resolve, 5));
                }
            };
            
            // 处理GIF完成事件
            gif.on('finished', (blob) => {
                resolve(blob);
            });
            
            gif.on('error', (error) => {
                reject(error);
            });
            
            // 开始生成
            generateFrames().then(() => {
                gif.render();
            }).catch(reject);
        });
    }
    
    // 更新压缩进度显示
    updateCompressionProgress(attempt, maxAttempts, currentSize = null) {
        const compressionStatus = document.getElementById('compressionStatus');
        const compressionText = document.getElementById('compressionText');
        
        compressionStatus.style.display = 'block';
        compressionStatus.className = 'compression-status';
        
        if (currentSize) {
            const sizeText = this.formatFileSize(currentSize);
            compressionText.textContent = `第${attempt}次压缩中... 当前大小: ${sizeText}`;
        } else {
            compressionText.textContent = `第${attempt}次压缩中...`;
        }
    }
    
    // 增强版压缩进度显示
    updateCompressionProgressEnhanced(stepName, currentStep, totalSteps, currentSize = null) {
        const compressionStatus = document.getElementById('compressionStatus');
        const compressionText = document.getElementById('compressionText');
        
        compressionStatus.style.display = 'block';
        compressionStatus.className = 'compression-status';
        
        const progress = Math.round((currentStep / totalSteps) * 100);
        
        if (currentSize) {
            const sizeText = this.formatFileSize(currentSize);
            const status = currentSize <= 1024 * 1024 ? '✅' : '🔄';
            compressionText.textContent = `${status} ${stepName} - ${sizeText} (${progress}%)`;
        } else {
            compressionText.textContent = `🔄 ${stepName}... (${progress}%)`;
        }
    }
    
    // 增强版压缩结果展示
    showCompressionResultEnhanced(success, originalSettings, finalSettings, finalSize, attempts, stepsUsed) {
        const compressionStatus = document.getElementById('compressionStatus');
        const compressionText = document.getElementById('compressionText');
        
        if (success) {
            compressionStatus.className = 'compression-status success';
            
            // 计算压缩详情
            const changes = [];
            if (finalSettings.quality !== originalSettings.quality) {
                changes.push(`质量:${originalSettings.quality}→${finalSettings.quality}`);
            }
            if (finalSettings.fps !== originalSettings.fps) {
                changes.push(`帧率:${originalSettings.fps}→${finalSettings.fps}fps`);
            }
            if (finalSettings.duration !== originalSettings.duration) {
                changes.push(`时长:${originalSettings.duration}→${finalSettings.duration}s`);
            }
            if (finalSettings.width !== originalSettings.width) {
                changes.push(`尺寸:${originalSettings.width}→${finalSettings.width}px`);
            }
            
            const finalSizeText = this.formatFileSize(finalSize);
            const changesText = changes.length > 0 ? ` (${changes.join(', ')})` : '';
            
            compressionText.textContent = `✅ 压缩成功！最终大小: ${finalSizeText}${changesText}`;
        } else {
            compressionStatus.className = 'compression-status error';
            compressionText.textContent = `❌ 无法压缩到1M以下，建议减少素材或时长`;
        }
        
        // 延长显示时间以便用户查看详情
        setTimeout(() => {
            compressionStatus.style.display = 'none';
        }, 5000);
    }
    
    // 显示压缩结果
    showCompressionResult(success, originalSize, finalSize, finalQuality, attempts) {
        const compressionStatus = document.getElementById('compressionStatus');
        const compressionText = document.getElementById('compressionText');
        
        if (success) {
            compressionStatus.className = 'compression-status success';
            const originalSizeText = this.formatFileSize(originalSize);
            const finalSizeText = this.formatFileSize(finalSize);
            const compressionRatio = ((originalSize - finalSize) / originalSize * 100).toFixed(1);
            
            if (attempts > 1) {
                compressionText.textContent = `✅ 压缩成功！${originalSizeText} → ${finalSizeText} (节省${compressionRatio}%)，质量: ${finalQuality}`;
            } else {
                compressionText.textContent = `✅ 文件已符合微信要求：${finalSizeText}`;
            }
        } else {
            compressionStatus.className = 'compression-status error';
            compressionText.textContent = `❌ 压缩失败，请尝试减少持续时间或素材数量`;
        }
        
        // 3秒后自动隐藏状态
        setTimeout(() => {
            compressionStatus.style.display = 'none';
        }, 3000);
    }
    
    // 参数调整辅助方法
    adjustSettings(originalSettings, adjustmentType, value) {
        const settings = { ...originalSettings };
        
        switch (adjustmentType) {
            case 'quality':
                settings.quality = value;
                break;
            case 'fps':
                settings.fps = value;
                break;
            case 'duration':
                settings.duration = Math.floor(originalSettings.duration * value);
                break;
        }
        
        return settings;
    }
    
    // 带设置的生成方法
    async generateWithSettings(settings) {
        return new Promise((resolve, reject) => {
            const totalFrames = settings.duration * settings.fps;
            
            // 创建GIF
            const gif = new GIF({
                workers: 2,
                quality: settings.quality,
                width: settings.width,
                height: settings.height,
                workerScript: 'js/gif.worker.js'
            });
            
            // 生成帧的异步函数
            const generateFrames = async () => {
                for (let i = 0; i < totalFrames; i++) {
                    // 更新动画时间
                    this.currentTime = (i / settings.fps);
                    this.animationState.time = this.currentTime;
                    
                    // 更新媒体索引
                    if (this.uploadedFiles.length > 1) {
                        this.updateCurrentMediaIndex();
                    }
                    
                    // 临时调整canvas尺寸用于渲染
                    const originalWidth = this.canvas.width;
                    const originalHeight = this.canvas.height;
                    
                    if (settings.width !== 300 || settings.height !== 300) {
                        this.canvas.width = settings.width;
                        this.canvas.height = settings.height;
                        this.ctx = this.canvas.getContext('2d');
                    }
                    
                    // 渲染当前帧
                    this.render();
                    
                    // 添加到GIF
                    gif.addFrame(this.canvas, { delay: Math.floor(1000 / settings.fps) });
                    
                    // 恢复原始canvas尺寸
                    if (settings.width !== 300 || settings.height !== 300) {
                        this.canvas.width = originalWidth;
                        this.canvas.height = originalHeight;
                        this.ctx = this.canvas.getContext('2d');
                    }
                    
                    // 让浏览器有时间更新UI
                    await new Promise(resolve => setTimeout(resolve, 3));
                }
            };
            
            // 处理GIF完成事件
            gif.on('finished', (blob) => {
                resolve({ blob, settings });
            });
            
            gif.on('error', (error) => {
                reject(error);
            });
            
            // 开始生成
            generateFrames().then(() => {
                gif.render();
            }).catch(reject);
        });
    }
    
    // 智能预估算法
    estimateOptimalSettings(baseSettings, targetSize) {
        const complexityFactor = this.uploadedFiles.length * 0.1 + 1;
        const currentEstimate = baseSettings.duration * baseSettings.fps * baseSettings.width * baseSettings.height * complexityFactor * 0.001;
        
        if (currentEstimate <= targetSize) {
            return baseSettings;
        }
        
        // 预估最优参数组合
        const ratio = targetSize / currentEstimate;
        const newSettings = { ...baseSettings };
        
        if (ratio > 0.7) {
            // 轻度压缩：仅调整质量
            newSettings.quality = Math.min(20, Math.max(1, Math.ceil(baseSettings.quality * 1.5)));
        } else if (ratio > 0.5) {
            // 中度压缩：质量+帧率
            newSettings.quality = 15;
            newSettings.fps = 8;
        } else {
            // 重度压缩：质量+帧率+时长调整（保持尺寸300×300）
            newSettings.quality = 18;
            newSettings.fps = 6;
            newSettings.duration = Math.floor(baseSettings.duration * 0.8);
        }
        
        return newSettings;
    }
    
    // 增强版智能自适应压缩算法
    async optimizeForWechatEnhanced(originalSettings) {
        const maxSize = 1024 * 1024; // 1MB
        const compressionSteps = [
            {
                type: 'quality',
                name: '质量优化',
                values: [10, 12, 15, 18, 20],
                impact: 'medium'
            },
            {
                type: 'fps',
                name: '帧率优化',
                values: [10, 8, 6],
                impact: 'high'
            },
            {
                type: 'duration',
                name: '时长优化',
                values: [1.0, 0.9, 0.8, 0.7],
                impact: 'high'
            }
        ];
        
        let currentSettings = { ...originalSettings };
        let bestResult = null;
        let totalAttempts = 0;
        
        // 智能预估起始点
        const estimatedSettings = this.estimateOptimalSettings(originalSettings, maxSize / 1024 / 1024);
        currentSettings = estimatedSettings;
        
        this.updateCompressionProgressEnhanced('预估最优参数', 0, compressionSteps.length);
        
        // 渐进式多维度压缩
        for (let stepIndex = 0; stepIndex < compressionSteps.length; stepIndex++) {
            const step = compressionSteps[stepIndex];
            this.updateCompressionProgressEnhanced(step.name, stepIndex + 1, compressionSteps.length);
            
            let stepSuccess = false;
            
            for (const value of step.values) {
                totalAttempts++;
                
                // 跳过当前值（避免重复测试）
                if ((step.type === 'quality' && value === currentSettings.quality) ||
                    (step.type === 'fps' && value === currentSettings.fps) ||
                    (step.type === 'duration' && value === 1.0 && currentSettings.duration === originalSettings.duration)) {
                    continue;
                }
                
                try {
                    const testSettings = this.adjustSettings(currentSettings, step.type, value);
                    const result = await this.generateWithSettings(testSettings);
                    
                    this.updateCompressionProgressEnhanced(
                        `${step.name}: ${this.formatFileSize(result.blob.size)}`,
                        stepIndex + 1,
                        compressionSteps.length,
                        result.blob.size
                    );
                    
                    if (result.blob.size <= maxSize) {
                        bestResult = result;
                        currentSettings = testSettings;
                        stepSuccess = true;
                        
                        // 如果已经达到目标，提前结束
                        this.showCompressionResultEnhanced(
                            true,
                            originalSettings,
                            bestResult.settings,
                            bestResult.blob.size,
                            totalAttempts,
                            stepIndex + 1
                        );
                        
                        return {
                            success: true,
                            blob: bestResult.blob,
                            settings: bestResult.settings,
                            originalSettings: originalSettings,
                            attempts: totalAttempts,
                            stepsUsed: stepIndex + 1
                        };
                    }
                    
                    // 保存当前最佳结果
                    if (!bestResult || result.blob.size < bestResult.blob.size) {
                        bestResult = result;
                        currentSettings = testSettings;
                    }
                    
                } catch (error) {
                    console.error(`压缩步骤 ${step.name} 值 ${value} 失败:`, error);
                    continue;
                }
            }
            
            // 如果当前步骤没有改善，继续下一步骤
            if (!stepSuccess && bestResult) {
                currentSettings = bestResult.settings;
            }
        }
        
        // 所有步骤完成后的最终结果
        if (bestResult) {
            const success = bestResult.blob.size <= maxSize;
            this.showCompressionResultEnhanced(
                success,
                originalSettings,
                bestResult.settings,
                bestResult.blob.size,
                totalAttempts,
                compressionSteps.length
            );
            
            return {
                success: success,
                blob: bestResult.blob,
                settings: bestResult.settings,
                originalSettings: originalSettings,
                attempts: totalAttempts,
                stepsUsed: compressionSteps.length
            };
        }
        
        // 完全失败的情况
        this.showCompressionResultEnhanced(false, originalSettings, originalSettings, 0, totalAttempts, compressionSteps.length);
        return {
            success: false,
            blob: null,
            error: '无法压缩到目标大小'
        };
    }
    
    // 旧版智能自适应压缩核心算法（保持向后兼容）
    async optimizeForWechat(originalQuality) {
        const maxSize = 1024 * 1024; // 1MB
        let currentQuality = originalQuality;
        let attempts = 0;
        const maxAttempts = 5;
        let firstBlob = null;
        
        while (attempts < maxAttempts) {
            attempts++;
            this.updateCompressionProgress(attempts, maxAttempts);
            
            try {
                const blob = await this.generateWithQuality(currentQuality);
                
                // 记录第一次生成的结果作为原始大小参考
                if (attempts === 1) {
                    firstBlob = blob;
                }
                
                this.updateCompressionProgress(attempts, maxAttempts, blob.size);
                
                // 检查是否满足大小要求
                if (blob.size <= maxSize) {
                    const originalSize = firstBlob ? firstBlob.size : blob.size;
                    this.showCompressionResult(true, originalSize, blob.size, currentQuality, attempts);
                    return {
                        success: true,
                        blob: blob,
                        finalQuality: currentQuality,
                        compressed: attempts > 1,
                        originalSize: originalSize,
                        finalSize: blob.size
                    };
                }
                
                // 如果是最后一次尝试，返回当前结果
                if (attempts >= maxAttempts) {
                    break;
                }
                
                // 智能质量调整算法
                const compressionRatio = blob.size / maxSize;
                const qualityReduction = Math.sqrt(compressionRatio);
                currentQuality = Math.min(20, Math.max(1, Math.ceil(currentQuality * qualityReduction)));
                
                // 避免质量调整过小的无效循环
                if (currentQuality >= 19) {
                    currentQuality = 20;
                    break;
                }
                
            } catch (error) {
                console.error(`压缩尝试 ${attempts} 失败:`, error);
                break;
            }
        }
        
        // 最后一次尝试使用最低质量
        try {
            const finalBlob = await this.generateWithQuality(20);
            const originalSize = firstBlob ? firstBlob.size : finalBlob.size;
            
            if (finalBlob.size <= maxSize) {
                this.showCompressionResult(true, originalSize, finalBlob.size, 20, attempts + 1);
                return {
                    success: true,
                    blob: finalBlob,
                    finalQuality: 20,
                    compressed: true,
                    originalSize: originalSize,
                    finalSize: finalBlob.size
                };
            } else {
                this.showCompressionResult(false, originalSize, finalBlob.size, 20, attempts + 1);
                return {
                    success: false,
                    blob: finalBlob,
                    finalQuality: 20,
                    compressed: true,
                    originalSize: originalSize,
                    finalSize: finalBlob.size
                };
            }
        } catch (error) {
            console.error('最终压缩尝试失败:', error);
            this.showCompressionResult(false, 0, 0, 20, attempts);
            return {
                success: false,
                blob: null,
                error: error
            };
        }
    }
    
    // 初始化自定义字体选择器
    initCustomFontSelector() {
        this.selectedFontFamily = 'Arial, sans-serif'; // 默认字体
        
        const header = document.getElementById('fontSelectorHeader');
        const dropdown = document.getElementById('fontOptionsDropdown');
        const options = dropdown.querySelectorAll('.font-option');
        
        // 点击头部切换下拉菜单
        header.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = header.classList.contains('active');
            
            if (isActive) {
                header.classList.remove('active');
                dropdown.style.display = 'none';
            } else {
                header.classList.add('active');
                dropdown.style.display = 'block';
            }
        });
        
        // 选择字体选项
        options.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const fontValue = option.dataset.value;
                const fontName = option.textContent;
                
                // 更新选中状态
                options.forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');
                
                // 更新头部显示
                const selectedFontSpan = header.querySelector('.selected-font');
                selectedFontSpan.textContent = fontName;
                selectedFontSpan.style.fontFamily = fontValue;
                
                // 更新应用设置
                this.selectedFontFamily = fontValue;
                this.updateTextSettings();
                
                // 关闭下拉菜单
                header.classList.remove('active');
                dropdown.style.display = 'none';
            });
        });
        
        // 点击外部关闭下拉菜单
        document.addEventListener('click', (e) => {
            if (!header.contains(e.target) && !dropdown.contains(e.target)) {
                header.classList.remove('active');
                dropdown.style.display = 'none';
            }
        });
    }
    
    updateGifSettings() {
        const duration = document.getElementById('gifDuration').value;
        const quality = document.getElementById('gifQuality').value;
        
        document.getElementById('durationValue').textContent = duration + 's';
        document.getElementById('qualityValue').textContent = quality;
    }
    
    async generateGif() {
        if (this.uploadedFiles.length === 0) {
            alert('请先上传图片或视频');
            return;
        }
        
        // 检查播放状态，如果暂停则提示用户先播放
        if (!this.isPlaying) {
            this.showPlayingWarning();
            return;
        }
        
        const generateBtn = document.getElementById('generateBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const wechatOptimize = document.getElementById('wechatOptimize').checked;
        
        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';
        progressContainer.style.display = 'block';
        
        try {
            const quality = parseInt(document.getElementById('gifQuality').value);
            
            if (wechatOptimize) {
                // 使用微信优化模式（增强版）
                progressText.textContent = '正在智能优化...';
                
                const duration = parseInt(document.getElementById('gifDuration').value);
                const originalSettings = {
                    quality: quality,
                    fps: 10,
                    duration: duration,
                    width: 300,
                    height: 300
                };
                
                const result = await this.optimizeForWechatEnhanced(originalSettings);
                
                if (result.success && result.blob) {
                    const url = URL.createObjectURL(result.blob);
                    this.showResult(url, result.blob.size, result.settings);
                    
                    this.generatedGifUrl = url;
                    this.generatedGifBlob = result.blob;
                } else {
                    // 即使压缩失败，也显示结果让用户选择
                    if (result.blob) {
                        const url = URL.createObjectURL(result.blob);
                        this.showResult(url, result.blob.size);
                        
                        this.generatedGifUrl = url;
                        this.generatedGifBlob = result.blob;
                    } else {
                        throw new Error('GIF生成失败');
                    }
                }
            } else {
                // 使用标准模式（原有逻辑）
                const duration = parseInt(document.getElementById('gifDuration').value);
                const fps = 10;
                const totalFrames = duration * fps;
                
                // 创建GIF
                const gif = new GIF({
                    workers: 2,
                    quality: quality,
                    width: 300,
                    height: 300,
                    workerScript: 'js/gif.worker.js'
                });
                
                // 生成帧
                for (let i = 0; i < totalFrames; i++) {
                    const progress = (i / totalFrames) * 100;
                    progressFill.style.width = progress + '%';
                    progressText.textContent = Math.round(progress) + '%';
                    
                    // 更新动画时间
                    this.currentTime = (i / fps);
                    this.animationState.time = this.currentTime;
                    
                    // 更新媒体索引（使用统一的切换逻辑）
                    if (this.uploadedFiles.length > 1) {
                        this.updateCurrentMediaIndex();
                    }
                    
                    // 渲染当前帧
                    this.render();
                    
                    // 添加到GIF
                    gif.addFrame(this.canvas, { delay: 100 });
                    
                    // 让浏览器有时间更新UI
                    await new Promise(resolve => setTimeout(resolve, 10));
                }
                
                // 渲染GIF
                gif.on('finished', (blob) => {
                    const url = URL.createObjectURL(blob);
                    this.showResult(url, blob.size);
                    
                    generateBtn.disabled = false;
                    generateBtn.textContent = '🎬 生成 GIF';
                    downloadBtn.disabled = false;
                    progressContainer.style.display = 'none';
                    
                    this.generatedGifUrl = url;
                    this.generatedGifBlob = blob;
                });
                
                gif.render();
                return; // 标准模式直接返回，等待gif.on('finished')回调
            }
            
            // 微信优化模式完成后重置UI状态
            generateBtn.disabled = false;
            generateBtn.textContent = '🎬 生成 GIF';
            downloadBtn.disabled = false;
            progressContainer.style.display = 'none';
            
        } catch (error) {
            console.error('生成GIF时出错:', error);
            alert('生成GIF时出错，请重试');
            
            generateBtn.disabled = false;
            generateBtn.textContent = '🎬 生成 GIF';
            progressContainer.style.display = 'none';
            
            // 隐藏压缩状态
            const compressionStatus = document.getElementById('compressionStatus');
            compressionStatus.style.display = 'none';
        }
    }
    
    showResult(url, fileSize, settings = null) {
        const resultSection = document.getElementById('resultSection');
        const resultGif = document.getElementById('resultGif');
        const fileSizeSpan = document.getElementById('fileSize');
        const fileDimensions = document.getElementById('fileDimensions');
        
        resultGif.src = url;
        fileSizeSpan.textContent = this.formatFileSize(fileSize);
        
        // 根据settings参数显示实际尺寸或默认尺寸
        if (settings && settings.width && settings.height) {
            fileDimensions.textContent = `${settings.width}×${settings.height}`;
        } else {
            fileDimensions.textContent = '300×300';
        }
        
        resultSection.style.display = 'block';
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    downloadGif() {
        if (!this.generatedGifUrl) return;
        
        const link = document.createElement('a');
        link.download = 'dynamic-emoji-' + Date.now() + '.gif';
        link.href = this.generatedGifUrl;
        link.click();
    }
    
    reset() {
        if (confirm('确定要重置所有设置吗？')) {
            // 清理上传的文件
            this.uploadedFiles.forEach(fileObj => {
                URL.revokeObjectURL(fileObj.url);
            });
            this.uploadedFiles = [];
            this.currentMediaIndex = 0;
            
            // 重置UI
            document.getElementById('fileList').innerHTML = '';
            document.getElementById('textInput').value = '';
            document.getElementById('fontSize').value = 24;
            document.getElementById('textColor').value = '#ffffff';
            // 重置自定义字体选择器
            this.selectedFontFamily = 'Arial, sans-serif';
            const fontHeader = document.getElementById('fontSelectorHeader');
            const selectedFontSpan = fontHeader.querySelector('.selected-font');
            selectedFontSpan.textContent = 'Arial';
            selectedFontSpan.style.fontFamily = 'Arial, sans-serif';
            
            // 重置选中状态
            const fontOptions = document.querySelectorAll('.font-option');
            fontOptions.forEach(opt => opt.classList.remove('selected'));
            const arialOption = document.querySelector('.font-option[data-value="Arial, sans-serif"]');
            if (arialOption) {
                arialOption.classList.add('selected');
            }
            document.getElementById('fontWeight').value = 'normal';
            document.getElementById('animationType').value = 'none';
            document.getElementById('textX').value = 200;
            document.getElementById('textY').value = 200;
            document.getElementById('gifDuration').value = 3;
            document.getElementById('gifQuality').value = 10;
            document.getElementById('wechatOptimize').checked = true;
            
            // 重置状态
            this.textSettings = {
                text: '',
                x: 200,
                y: 200,
                fontSize: 24,
                color: '#ffffff',
                fontFamily: 'Arial, sans-serif',
                fontWeight: 'normal',
                animationType: 'none'
            };
            
            this.animationState = {
                time: 0,
                bounceOffset: 0,
                fadeOpacity: 1,
                rotateAngle: 0,
                shakeOffset: 0,
                typewriterIndex: 0
            };
            
            // 隐藏结果和压缩状态
            document.getElementById('resultSection').style.display = 'none';
            document.getElementById('downloadBtn').disabled = true;
            document.getElementById('compressionStatus').style.display = 'none';
            
            // 清理生成的GIF
            if (this.generatedGifUrl) {
                URL.revokeObjectURL(this.generatedGifUrl);
                this.generatedGifUrl = null;
                this.generatedGifBlob = null;
            }
            
            // 暂停播放并重绘
            this.pause();
            this.drawPlaceholder();
            
            // 更新显示值
            document.getElementById('fontSizeValue').textContent = '24px';
            document.getElementById('durationValue').textContent = '3s';
            document.getElementById('qualityValue').textContent = '10';
        }
    }
    
    // 显示视频抽帧模态框
    showFrameExtractionModal(fileIndex) {
        const fileObj = this.uploadedFiles[fileIndex];
        if (!fileObj || fileObj.type !== 'video' || !fileObj.element) {
            alert('无效的视频文件');
            return;
        }
        
        const modal = document.getElementById('frameExtractionModal');
        const video = fileObj.element;
        
        // 设置当前处理的视频
        this.currentExtractionFile = {
            index: fileIndex,
            fileObj: fileObj,
            video: video
        };
        
        // 重置模态框状态
        this.resetModalState();
        
        // 显示视频信息
        this.updateVideoInfo(video);
        
        // 显示模态框
        modal.style.display = 'flex';
        
        // 设置事件监听器
        this.setupModalEventListeners();
    }
    
    // 重置模态框状态
    resetModalState() {
        // 重置输入值
        document.getElementById('frameInterval').value = 1;
        document.getElementById('maxFrames').value = 20;
        document.getElementById('frameIntervalValue').textContent = '1.0s';
        document.getElementById('maxFramesValue').textContent = '20帧';
        
        // 清空预览网格
        document.getElementById('framePreviewGrid').innerHTML = '<div class="frame-preview-empty">点击"预览抽帧"查看提取的帧</div>';
        
        // 重置按钮状态
        document.getElementById('extractFramesBtn').disabled = true;
        document.getElementById('previewFramesBtn').disabled = false;
        
        // 隐藏进度条
        document.getElementById('extractionProgress').style.display = 'none';
        
        // 清理之前的预览帧
        if (this.previewFrames) {
            this.previewFrames.forEach(frame => {
                if (frame.url) URL.revokeObjectURL(frame.url);
            });
            this.previewFrames = [];
        }
    }
    
    // 更新视频信息显示
    updateVideoInfo(video) {
        const duration = video.duration || 0;
        const durationText = duration > 0 ? `${duration.toFixed(1)}秒` : '未知';
        document.getElementById('videoDuration').textContent = durationText;
        
        // 计算预计抽帧数
        this.updateEstimatedFrames();
    }
    
    // 更新预计抽帧数
    updateEstimatedFrames() {
        const video = this.currentExtractionFile?.video;
        if (!video || !video.duration) {
            document.getElementById('estimatedFrames').textContent = '-';
            return;
        }
        
        const interval = parseFloat(document.getElementById('frameInterval').value);
        const maxFrames = parseInt(document.getElementById('maxFrames').value);
        const duration = video.duration;
        
        const possibleFrames = Math.floor(duration / interval) + 1;
        const actualFrames = Math.min(possibleFrames, maxFrames);
        
        document.getElementById('estimatedFrames').textContent = `${actualFrames}帧`;
    }
    
    // 设置模态框事件监听器
    setupModalEventListeners() {
        // 避免重复绑定
        if (this.modalListenersSetup) return;
        this.modalListenersSetup = true;
        
        // 关闭模态框
        document.getElementById('closeFrameModal').addEventListener('click', () => {
            this.closeFrameExtractionModal();
        });
        
        document.getElementById('cancelExtractionBtn').addEventListener('click', () => {
            this.closeFrameExtractionModal();
        });
        
        // 点击模态框外部关闭
        document.getElementById('frameExtractionModal').addEventListener('click', (e) => {
            if (e.target.id === 'frameExtractionModal') {
                this.closeFrameExtractionModal();
            }
        });
        
        // 抽帧间隔变化
        document.getElementById('frameInterval').addEventListener('input', (e) => {
            document.getElementById('frameIntervalValue').textContent = parseFloat(e.target.value).toFixed(1) + 's';
            this.updateEstimatedFrames();
        });
        
        // 最大抽帧数变化
        document.getElementById('maxFrames').addEventListener('input', (e) => {
            document.getElementById('maxFramesValue').textContent = e.target.value + '帧';
            this.updateEstimatedFrames();
        });
        
        // 预览抽帧
        document.getElementById('previewFramesBtn').addEventListener('click', () => {
            this.previewFrameExtraction();
        });
        
        // 确认抽帧
        document.getElementById('extractFramesBtn').addEventListener('click', () => {
            this.extractFramesFromVideo();
        });
    }
    
    // 关闭抽帧模态框
    closeFrameExtractionModal() {
        const modal = document.getElementById('frameExtractionModal');
        modal.style.display = 'none';
        
        // 清理资源
        if (this.previewFrames) {
            this.previewFrames.forEach(frame => {
                if (frame.url) URL.revokeObjectURL(frame.url);
            });
            this.previewFrames = [];
        }
        
        this.currentExtractionFile = null;
    }
    
    // 预览抽帧
    async previewFrameExtraction() {
        if (!this.currentExtractionFile) return;
        
        const video = this.currentExtractionFile.video;
        const interval = parseFloat(document.getElementById('frameInterval').value);
        const maxFrames = parseInt(document.getElementById('maxFrames').value);
        
        // 验证视频状态
        if (!video.duration || video.duration === 0) {
            alert('视频未完全加载，请稍后重试');
            return;
        }
        
        // 计算抽帧时间点
        const timePoints = this.calculateFrameTimePoints(video.duration, interval, maxFrames);
        
        if (timePoints.length === 0) {
            alert('无法计算抽帧时间点，请检查设置参数');
            return;
        }
        
        // 禁用相关按钮并显示进度
        const previewBtn = document.getElementById('previewFramesBtn');
        const extractBtn = document.getElementById('extractFramesBtn');
        const grid = document.getElementById('framePreviewGrid');
        
        previewBtn.disabled = true;
        previewBtn.textContent = '生成预览中...';
        extractBtn.disabled = true;
        
        // 显示处理进度
        grid.innerHTML = '<div class="frame-preview-empty">正在生成预览，请稍候...</div>';
        
        try {
            // 清理之前的预览帧
            if (this.previewFrames) {
                this.previewFrames.forEach(frame => {
                    if (frame.url) URL.revokeObjectURL(frame.url);
                });
            }
            
            this.previewFrames = [];
            
            // 逐个生成预览帧
            for (let i = 0; i < timePoints.length; i++) {
                const time = timePoints[i];
                
                // 更新进度提示
                grid.innerHTML = `<div class="frame-preview-empty">正在生成预览 ${i + 1}/${timePoints.length}...</div>`;
                
                try {
                    const canvas = await this.createCanvasFromVideoFrame(video, time);
                    const dataURL = canvas.toDataURL('image/png', 0.95);
                    
                    // 验证DataURL是否有效
                    if (!dataURL || dataURL === 'data:,') {
                        throw new Error('Canvas转换为DataURL失败');
                    }
                    
                    this.previewFrames.push({
                        time: time,
                        canvas: canvas,
                        dataURL: dataURL,
                        url: dataURL // 兼容现有显示代码
                    });
                    
                    console.log(`预览帧 ${i + 1} 创建成功: ${time}s, DataURL长度: ${dataURL.length}`);
                    
                    // 每生成几帧就更新一次显示
                    if ((i + 1) % 3 === 0 || i === timePoints.length - 1) {
                        this.updatePreviewGrid();
                    }
                    
                } catch (frameError) {
                    console.warn(`第 ${i + 1} 帧生成失败:`, frameError);
                    // 跳过失败的帧，继续处理下一帧
                }
                
                // 给UI更新的时间
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            // 最终更新预览显示
            this.updatePreviewGrid();
            
            if (this.previewFrames.length > 0) {
                // 启用确认抽帧按钮
                extractBtn.disabled = false;
                console.log(`成功生成 ${this.previewFrames.length} 个预览帧`);
            } else {
                grid.innerHTML = '<div class="frame-preview-empty">预览生成失败，请重试</div>';
            }
            
        } catch (error) {
            console.error('预览抽帧失败:', error);
            grid.innerHTML = '<div class="frame-preview-empty">预览生成失败，请重试</div>';
            alert(`预览抽帧失败: ${error.message}`);
        } finally {
            // 恢复预览按钮
            previewBtn.disabled = false;
            previewBtn.textContent = '🔍 预览抽帧';
        }
    }
    
    // 计算抽帧时间点
    calculateFrameTimePoints(duration, interval, maxFrames) {
        const timePoints = [];
        let currentTime = 0;
        
        while (currentTime <= duration && timePoints.length < maxFrames) {
            timePoints.push(Math.min(currentTime, duration - 0.1)); // 避免超出视频时长
            currentTime += interval;
        }
        
        return timePoints;
    }
    
    // 从视频特定时间点创建canvas
    createCanvasFromVideoFrame(video, time) {
        return new Promise((resolve, reject) => {
            // 验证输入参数
            if (!video || !video.videoWidth || !video.videoHeight) {
                reject(new Error('无效的视频对象'));
                return;
            }
            
            if (time < 0 || time > video.duration) {
                reject(new Error(`无效的时间点: ${time}，视频时长: ${video.duration}`));
                return;
            }
            
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // 设置canvas尺寸为项目标准尺寸
            canvas.width = 300;
            canvas.height = 300;
            
            // 保存视频原始状态
            const wasPlaying = !video.paused;
            const originalTime = video.currentTime;
            
            let timeoutId;
            let seekedHandler;
            
            const cleanup = () => {
                if (timeoutId) clearTimeout(timeoutId);
                if (seekedHandler) video.removeEventListener('seeked', seekedHandler);
            };
            
            const restoreVideoState = () => {
                try {
                    video.currentTime = originalTime;
                    if (wasPlaying) {
                        video.play().catch(err => {
                            console.warn('恢复播放失败:', err);
                        });
                    }
                } catch (err) {
                    console.warn('恢复视频状态失败:', err);
                }
            };
            
            // 创建seeked事件处理器
            seekedHandler = () => {
                cleanup();
                
                try {
                    // 验证视频已跳转到正确时间（允许0.1秒误差）
                    if (Math.abs(video.currentTime - time) > 0.1) {
                        console.warn(`视频时间跳转不准确: 期望${time}s, 实际${video.currentTime}s`);
                    }
                    
                    // 计算视频在1:1画布中的缩放和位置
                    const videoWidth = video.videoWidth;
                    const videoHeight = video.videoHeight;
                    
                    // 计算居中裁剪参数
                    const scale = Math.max(300 / videoWidth, 300 / videoHeight);
                    const scaledWidth = videoWidth * scale;
                    const scaledHeight = videoHeight * scale;
                    const x = (300 - scaledWidth) / 2;
                    const y = (300 - scaledHeight) / 2;
                    
                    // 清空画布并设置背景
                    ctx.clearRect(0, 0, 300, 300);
                    ctx.fillStyle = '#f8f9fa';
                    ctx.fillRect(0, 0, 300, 300);
                    
                    // 绘制视频帧
                    ctx.drawImage(video, x, y, scaledWidth, scaledHeight);
                    
                    // 验证Canvas内容是否有效
                    const imageData = ctx.getImageData(0, 0, 300, 300);
                    const hasContent = imageData.data.some((value, index) => {
                        // 跳过alpha通道，检查RGB是否有非背景色数据
                        if (index % 4 === 3) return false;
                        return value !== 248 && value !== 249 && value !== 250; // 背景色#f8f9fa的RGB值
                    });
                    
                    if (!hasContent) {
                        console.warn('Canvas内容似乎为空，但继续处理');
                    }
                    
                    console.log(`成功抽取视频帧: 时间${time}s, Canvas尺寸${canvas.width}x${canvas.height}`);
                    
                    // 恢复视频状态后返回Canvas
                    restoreVideoState();
                    resolve(canvas);
                    
                } catch (error) {
                    console.error('绘制视频帧失败:', error);
                    restoreVideoState();
                    reject(error);
                }
            };
            
            // 添加超时机制
            timeoutId = setTimeout(() => {
                cleanup();
                restoreVideoState();
                reject(new Error(`视频抽帧超时: ${time}s`));
            }, 10000); // 增加到10秒超时
            
            // 监听seeked事件
            video.addEventListener('seeked', seekedHandler);
            
            try {
                // 暂停视频并跳转到指定时间
                video.pause();
                
                // 使用更精确的时间设置
                const targetTime = Math.min(Math.max(time, 0), video.duration - 0.1);
                video.currentTime = targetTime;
                
                console.log(`开始抽帧: 跳转到${targetTime}s`);
                
            } catch (error) {
                cleanup();
                restoreVideoState();
                reject(new Error(`设置视频时间失败: ${error.message}`));
            }
        });
    }
    
    // 注：convertCanvasToImageFile方法已移除，现在直接使用DataURL
    
    // 更新预览网格显示
    updatePreviewGrid() {
        const grid = document.getElementById('framePreviewGrid');
        grid.innerHTML = '';
        
        if (!this.previewFrames || this.previewFrames.length === 0) {
            grid.innerHTML = '<div class="frame-preview-empty">暂无预览帧</div>';
            return;
        }
        
        this.previewFrames.forEach((frame, index) => {
            const item = document.createElement('div');
            item.className = 'frame-preview-item';
            
            item.innerHTML = `
                <img src="${frame.url}" alt="Frame ${index + 1}" class="frame-preview-img">
                <div class="frame-preview-info">
                    <div class="frame-preview-time">${frame.time.toFixed(1)}s</div>
                    <div>帧 ${index + 1}</div>
                </div>
            `;
            
            grid.appendChild(item);
        });
    }
    
    // 核心抽帧方法
    async extractFramesFromVideo() {
        if (!this.previewFrames || this.previewFrames.length === 0) {
            alert('请先预览抽帧');
            return;
        }
        
        const fileObj = this.currentExtractionFile.fileObj;
        const baseName = fileObj.name.replace(/\.[^/.]+$/, ''); // 移除扩展名
        
        // 显示进度
        const progressContainer = document.getElementById('extractionProgress');
        const progressFill = document.getElementById('extractionProgressFill');
        const progressText = document.getElementById('extractionProgressText');
        
        progressContainer.style.display = 'block';
        document.getElementById('extractFramesBtn').disabled = true;
        
        const extractedFrames = [];
        
        try {
            for (let i = 0; i < this.previewFrames.length; i++) {
                const frame = this.previewFrames[i];
                const progress = ((i + 1) / this.previewFrames.length) * 100;
                
                // 更新进度
                progressFill.style.width = progress + '%';
                progressText.textContent = `正在抽帧... ${Math.round(progress)}%`;
                
                // 生成文件名
                const filename = `${baseName}_frame_${String(i + 1).padStart(3, '0')}.png`;
                
                // 直接使用DataURL，无需转换为File对象
                if (frame.dataURL) {
                    extractedFrames.push({
                        filename: filename,
                        dataURL: frame.dataURL,
                        time: frame.time,
                        originalVideoIndex: this.currentExtractionFile.index,
                        canvas: frame.canvas // 保留canvas引用以备用
                    });
                    
                    console.log(`抽帧 ${i + 1} 准备完成: ${filename}, DataURL长度: ${frame.dataURL.length}`);
                } else {
                    console.warn(`第 ${i + 1} 帧DataURL无效，跳过`);
                }
                
                // 让UI有时间更新
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            
            // 添加抽取的帧到文件列表
            await this.addExtractedFramesToFileList(extractedFrames);
            
            // 显示成功消息
            alert(`成功抽取了 ${extractedFrames.length} 帧图片`);
            
            // 关闭模态框
            this.closeFrameExtractionModal();
            
        } catch (error) {
            console.error('抽帧失败:', error);
            alert('抽帧失败，请重试');
        } finally {
            progressContainer.style.display = 'none';
            document.getElementById('extractFramesBtn').disabled = false;
        }
    }
    
    // 将抽取的帧添加到文件列表
    async addExtractedFramesToFileList(frames) {
        const addedIndices = []; // 记录添加的文件索引
        
        for (const frameData of frames) {
            if (!frameData.dataURL || !frameData.filename) {
                console.warn('跳过无效的抽取帧', frameData);
                continue;
            }
            
            // 估算DataURL对应的文件大小（Base64编码大约是原始大小的4/3）
            const estimatedSize = Math.round((frameData.dataURL.length - 22) * 0.75); // 减去data:image/png;base64,前缀
            
            // 创建文件对象，标记为抽取帧
            const fileObj = {
                name: frameData.filename,
                size: this.formatFileSize(estimatedSize),
                type: 'image',
                dataURL: frameData.dataURL, // 直接使用DataURL
                url: frameData.dataURL, // 兼容性URL
                element: null,
                isExtractedFrame: true, // 标记为抽取帧
                extractedFrom: frameData.originalVideoIndex, // 原视频索引
                frameTime: frameData.time, // 抽取时间点
                ready: false // 加载状态标记
            };
            
            // 添加到文件列表
            const newIndex = this.uploadedFiles.length;
            this.uploadedFiles.push(fileObj);
            addedIndices.push(newIndex);
            
            console.log(`添加抽取帧到列表: ${frameData.filename} (索引: ${newIndex}, DataURL长度: ${frameData.dataURL.length})`);
            
            try {
                // 创建图片元素
                await this.createMediaElement(fileObj);
                console.log(`抽取帧准备完成: ${frameData.filename}`);
            } catch (error) {
                console.error(`抽取帧创建失败: ${frameData.filename}`, error);
                fileObj.error = '创建失败';
            }
        }
        
        // 更新文件列表显示
        this.updateFileList();
        
        // 如果添加了文件，更新当前显示和播放状态
        if (addedIndices.length > 0) {
            // 如果这是第一批文件，从第一个开始播放
            if (this.uploadedFiles.length === frames.length) {
                this.currentMediaIndex = 0;
                this.currentTime = 0; // 重置时间
                this.play();
            } else {
                // 如果已有文件在播放，继续当前播放状态
                if (this.isPlaying) {
                    // 重新渲染以包含新的抽取帧
                    this.render();
                } else {
                    // 如果没在播放，渲染当前帧
                    this.render();
                }
            }
            
            console.log(`成功添加 ${addedIndices.length} 个抽取帧到文件列表，当前总文件数: ${this.uploadedFiles.length}`);
        }
    }

    // ======================== 工具方法 ========================
    
    throttle(func, delay) {
        let timeoutId;
        let lastExecTime = 0;
        return function (...args) {
            const currentTime = Date.now();
            
            if (currentTime - lastExecTime > delay) {
                func.apply(this, args);
                lastExecTime = currentTime;
            } else {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => {
                    func.apply(this, args);
                    lastExecTime = Date.now();
                }, delay - (currentTime - lastExecTime));
            }
        };
    }
    
    updatePreviewPositionOnScroll() {
        try {
            if (!this.previewState?.isVisible || !this.previewState?.currentElement) {
                return;
            }
            
            const previewContainer = document.getElementById('filePreview');
            if (!previewContainer || previewContainer.style.display !== 'block') {
                return;
            }
            
            // 检查元素是否仍在DOM中
            if (!document.contains(this.previewState.currentElement)) {
                this.hideFilePreview();
                return;
            }
            
            // 重新计算位置
            const mockEvent = {
                target: this.previewState.currentElement
            };
            this.positionAndShowPreview(previewContainer, mockEvent);
            
        } catch (error) {
            console.error('滚动时更新预览位置失败:', error);
            this.hideFilePreview();
        }
    }
    
    // 检查位置是否在当前视窗内完全可见（使用视窗坐标系）
    isPositionVisible(left, top, width, height) {
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        // 视窗边界（纯视窗坐标系，不添加滚动偏移）
        const viewportLeft = 0;
        const viewportTop = 0;
        const viewportRight = viewportWidth;
        const viewportBottom = viewportHeight;
        
        // 计算预览框的边界
        const previewLeft = left;
        const previewTop = top;
        const previewRight = left + width;
        const previewBottom = top + height;
        
        // 检查预览框是否完全在当前视窗内
        const isInViewport = (
            previewLeft >= viewportLeft &&
            previewTop >= viewportTop &&
            previewRight <= viewportRight &&
            previewBottom <= viewportBottom
        );
        
        console.log(`[可见性检查] 预览框边界: (${previewLeft}, ${previewTop}, ${previewRight}, ${previewBottom})`);
        console.log(`[可见性检查] 视窗边界: (${viewportLeft}, ${viewportTop}, ${viewportRight}, ${viewportBottom})`);
        console.log(`[可见性检查] 完全可见: ${isInViewport}`);
        
        // 额外的安全边距检查（至少保留5px边距）
        const safeMargin = 5;
        const isSafelyVisible = (
            previewLeft >= viewportLeft + safeMargin &&
            previewTop >= viewportTop + safeMargin &&
            previewRight <= viewportRight - safeMargin &&
            previewBottom <= viewportBottom - safeMargin
        );
        
        console.log(`[可见性检查] 安全可见(含5px边距): ${isSafelyVisible}`);
        
        return isSafelyVisible;
    }
    
    // 计算最优预览位置（使用视窗坐标系）
    calculateOptimalPosition(targetRect) {
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        const containerWidth = 200;
        const containerHeight = 200;
        const margin = 10;
        
        console.log(`[位置计算] 目标元素(视窗坐标): (${targetRect.left}, ${targetRect.top}, ${targetRect.right}, ${targetRect.bottom})`);
        console.log(`[位置计算] 视窗尺寸: ${viewportWidth}x${viewportHeight}`);
        
        // 计算元素在视窗中的相对位置，用于智能选择策略
        const elementCenterY = targetRect.top + targetRect.height / 2;
        const viewportCenterY = viewportHeight / 2;
        const isInLowerHalf = elementCenterY > viewportCenterY;
        
        console.log(`[位置计算] 元素位置分析: 中心Y=${elementCenterY}, 视窗中心Y=${viewportCenterY}, 在下半部分=${isInLowerHalf}`);
        
        // 根据元素位置动态调整策略优先级
        let strategies;
        if (isInLowerHalf) {
            // 元素在下半部分，优先使用上方位置
            console.log(`[位置计算] 使用下半部分优化策略（优先上方）`);
            strategies = [
                {
                    name: '上方',
                    calculate: () => ({
                        left: targetRect.left,
                        top: targetRect.top - containerHeight - margin
                    })
                },
                {
                    name: '右上角',
                    calculate: () => ({
                        left: targetRect.right + margin,
                        top: targetRect.top - containerHeight - margin
                    })
                },
                {
                    name: '左上角',
                    calculate: () => ({
                        left: targetRect.left - containerWidth - margin,
                        top: targetRect.top - containerHeight - margin
                    })
                },
                {
                    name: '右侧',
                    calculate: () => ({
                        left: targetRect.right + margin,
                        top: targetRect.top
                    })
                },
                {
                    name: '左侧',
                    calculate: () => ({
                        left: targetRect.left - containerWidth - margin,
                        top: targetRect.top
                    })
                },
                {
                    name: '居中',
                    calculate: () => ({
                        left: (viewportWidth - containerWidth) / 2,
                        top: (viewportHeight - containerHeight) / 2
                    })
                }
            ];
        } else {
            // 元素在上半部分，使用常规策略
            console.log(`[位置计算] 使用上半部分常规策略`);
            strategies = [
                {
                    name: '右侧',
                    calculate: () => ({
                        left: targetRect.right + margin,
                        top: targetRect.top
                    })
                },
                {
                    name: '左侧',
                    calculate: () => ({
                        left: targetRect.left - containerWidth - margin,
                        top: targetRect.top
                    })
                },
                {
                    name: '下方',
                    calculate: () => ({
                        left: targetRect.left,
                        top: targetRect.bottom + margin
                    })
                },
                {
                    name: '上方',
                    calculate: () => ({
                        left: targetRect.left,
                        top: targetRect.top - containerHeight - margin
                    })
                },
                {
                    name: '右上角',
                    calculate: () => ({
                        left: targetRect.right + margin,
                        top: targetRect.top - containerHeight - margin
                    })
                },
                {
                    name: '左上角',
                    calculate: () => ({
                        left: targetRect.left - containerWidth - margin,
                        top: targetRect.top - containerHeight - margin
                    })
                },
                {
                    name: '居中',
                    calculate: () => ({
                        left: (viewportWidth - containerWidth) / 2,
                        top: (viewportHeight - containerHeight) / 2
                    })
                }
            ];
        }
        
        // 测试每个策略，选择第一个可见的位置
        for (const strategy of strategies) {
            const position = strategy.calculate();
            console.log(`[位置计算] 测试策略: ${strategy.name} => (${position.left}, ${position.top})`);
            
            if (this.isPositionVisible(position.left, position.top, containerWidth, containerHeight)) {
                console.log(`[位置计算] 选择策略: ${strategy.name}`);
                return {
                    left: position.left,
                    top: position.top,
                    strategy: strategy.name
                };
            }
        }
        
        // 如果没有完全可见的位置，使用智能后备策略
        console.log(`[位置计算] 所有策略都不可见，使用智能后备策略`);
        
        // 强制居中，但确保不会超出视窗边界
        const safeMargin = 10;
        const centeredLeft = Math.max(
            safeMargin,
            Math.min(
                (viewportWidth - containerWidth) / 2,
                viewportWidth - containerWidth - safeMargin
            )
        );
        const centeredTop = Math.max(
            safeMargin,
            Math.min(
                (viewportHeight - containerHeight) / 2,
                viewportHeight - containerHeight - safeMargin
            )
        );
        
        console.log(`[位置计算] 智能后备位置: (${centeredLeft}, ${centeredTop})`);
        
        return {
            left: centeredLeft,
            top: centeredTop,
            strategy: '智能居中(后备)'
        };
    }

    // ======================== 简化预览系统 ========================
    
    showFilePreview(fileObj, event) {
        try {
            console.log(`[预览调试] 开始显示预览 - 文件: ${fileObj?.name}, 类型: ${fileObj?.type}, 索引: ${fileObj?.index || 'unknown'}`);
            
            const previewContainer = document.getElementById('filePreview');
            const previewImage = document.getElementById('previewImage');
            
            if (!previewContainer || !previewImage || !fileObj || !event?.target) {
                console.log(`[预览调试] 预检查失败 - 容器: ${!!previewContainer}, 图片: ${!!previewImage}, 文件: ${!!fileObj}, 事件: ${!!event?.target}`);
                return;
            }
            
            // 记录触发元素信息
            const rect = event.target.getBoundingClientRect();
            console.log(`[预览调试] 触发元素位置: left=${rect.left}, top=${rect.top}, right=${rect.right}, bottom=${rect.bottom}`);
            
            // 只为图片显示预览
            if (fileObj.type === 'image') {
                console.log(`[预览调试] 图片文件确认 - 是否抽取帧: ${fileObj.isExtractedFrame}`);
                
                // 先隐藏之前的预览
                if (this.previewState.isVisible) {
                    console.log(`[预览调试] 隐藏之前的预览`);
                    this.hideFilePreview();
                }
                
                // 更新预览状态
                this.previewState.isVisible = true;
                this.previewState.currentElement = event.target;
                this.previewState.currentFileObj = fileObj;
                
                // 设置图片源
                const imageSrc = fileObj.isExtractedFrame ? 
                    (fileObj.dataURL || fileObj.url) : fileObj.url;
                
                console.log(`[预览调试] 图片源: ${imageSrc ? '有效' : '无效'}, 长度: ${imageSrc?.length || 0}`);
                
                if (!imageSrc) {
                    console.warn('图片源为空，无法显示预览');
                    return;
                }
                
                // 预加载图片以确保显示正常
                const tempImg = new Image();
                tempImg.onload = () => {
                    console.log(`[预览调试] 图片预加载成功 - 尺寸: ${tempImg.width}x${tempImg.height}`);
                    previewImage.src = imageSrc;
                    this.positionAndShowPreview(previewContainer, event);
                };
                tempImg.onerror = () => {
                    console.warn('[预览调试] 图片加载失败:', imageSrc.substring(0, 100) + '...');
                    this.hideFilePreview();
                };
                tempImg.src = imageSrc;
            } else {
                console.log(`[预览调试] 非图片文件，跳过预览 - 类型: ${fileObj.type}`);
            }
        } catch (error) {
            console.error('[预览调试] 显示文件预览失败:', error);
            this.hideFilePreview();
        }
    }
    
    positionAndShowPreview(container, event) {
        try {
            console.log(`[位置调试] 开始计算预览框位置`);
            
            if (!container || !event?.target) {
                console.log(`[位置调试] 参数检查失败 - 容器: ${!!container}, 事件: ${!!event?.target}`);
                return;
            }
            
            const rect = event.target.getBoundingClientRect();
            console.log(`[位置调试] 目标元素边界: left=${rect.left}, top=${rect.top}, right=${rect.right}, bottom=${rect.bottom}, width=${rect.width}, height=${rect.height}`);
            
            // 添加坐标系统验证信息
            const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
            const scrollY = window.pageYOffset || document.documentElement.scrollTop;
            console.log(`[坐标验证] 当前滚动位置: scrollX=${scrollX}, scrollY=${scrollY}`);
            console.log(`[坐标验证] 视窗尺寸: width=${window.innerWidth}, height=${window.innerHeight}`);
            console.log(`[坐标验证] getBoundingClientRect返回视窗坐标，无需添加滚动偏移`);
            
            // 检查元素是否在视窗内
            if (rect.width === 0 || rect.height === 0) {
                console.log(`[位置调试] 元素尺寸无效，跳过`);
                return;
            }
            
            // 使用新的智能位置计算
            const optimalPosition = this.calculateOptimalPosition(rect);
            console.log(`[位置调试] 智能位置计算结果: (${optimalPosition.left}, ${optimalPosition.top}) 策略: ${optimalPosition.strategy}`);
            
            // 应用位置
            const finalLeft = Math.round(optimalPosition.left);
            const finalTop = Math.round(optimalPosition.top);
            container.style.left = finalLeft + 'px';
            container.style.top = finalTop + 'px';
            container.style.display = 'block';
            
            console.log(`[位置调试] 最终位置应用: left=${finalLeft}px, top=${finalTop}px, display=block`);
            
            // 验证最终位置的可见性
            const isActuallyVisible = this.isPositionVisible(finalLeft, finalTop, 200, 200);
            console.log(`[位置调试] 最终位置可见性验证: ${isActuallyVisible}`);
            
        } catch (error) {
            console.error('[位置调试] 定位预览框失败:', error);
        }
    }
    
    hideFilePreview() {
        try {
            const previewContainer = document.getElementById('filePreview');
            const previewImage = document.getElementById('previewImage');
            
            if (previewContainer) {
                previewContainer.style.display = 'none';
            }
            
            // 清理图片源，释放内存
            if (previewImage) {
                previewImage.src = '';
            }
            
            // 清理预览状态
            this.previewState.isVisible = false;
            this.previewState.currentElement = null;
            this.previewState.currentFileObj = null;
            
        } catch (error) {
            console.error('隐藏预览失败:', error);
        }
    }
    
    setupFilePreviewListeners() {
        console.log(`[事件调试] 开始设置预览事件监听器`);
        
        // 先清理之前的监听器（如果有的话）
        this.cleanupFilePreviewListeners();
        
        const fileNames = document.querySelectorAll('.file-name[data-file-index]');
        console.log(`[事件调试] 找到 ${fileNames.length} 个文件名元素`);
        
        // 存储事件处理函数引用，便于后续清理
        this.previewEventHandlers = [];
        
        fileNames.forEach((fileName, index) => {
            const fileIndex = parseInt(fileName.dataset.fileIndex);
            const fileObj = this.uploadedFiles[fileIndex];
            
            console.log(`[事件调试] 处理第 ${index + 1} 个元素 - 文件索引: ${fileIndex}, 文件名: ${fileObj?.name || '未知'}, 类型: ${fileObj?.type || '未知'}`);
            
            if (!fileObj) {
                console.warn(`[事件调试] 跳过无效文件对象 - 索引: ${fileIndex}`);
                return;
            }
            
            // 验证元素属性
            const elementInfo = {
                tagName: fileName.tagName,
                className: fileName.className,
                textContent: fileName.textContent?.substring(0, 50) + '...',
                hasDataIndex: fileName.hasAttribute('data-file-index'),
                dataIndex: fileName.dataset.fileIndex
            };
            console.log(`[事件调试] 元素信息:`, elementInfo);
            
            // 创建事件处理函数
            const mouseEnterHandler = (event) => {
                console.log(`[事件调试] mouseenter 触发 - 文件: ${fileObj.name}`);
                this.showFilePreview(fileObj, event);
            };
            
            const mouseLeaveHandler = () => {
                console.log(`[事件调试] mouseleave 触发 - 文件: ${fileObj.name}`);
                this.hideFilePreview();
            };
            
            const mouseMoveHandler = (event) => {
                const previewContainer = document.getElementById('filePreview');
                if (previewContainer && previewContainer.style.display === 'block') {
                    this.positionAndShowPreview(previewContainer, event);
                }
            };
            
            try {
                // 添加事件监听器
                fileName.addEventListener('mouseenter', mouseEnterHandler);
                fileName.addEventListener('mouseleave', mouseLeaveHandler);
                fileName.addEventListener('mousemove', mouseMoveHandler);
                
                console.log(`[事件调试] 成功绑定事件监听器 - 文件: ${fileObj.name}`);
                
                // 存储引用便于清理
                this.previewEventHandlers.push({
                    element: fileName,
                    fileObj: fileObj, // 添加文件引用便于调试
                    events: [
                        { type: 'mouseenter', handler: mouseEnterHandler },
                        { type: 'mouseleave', handler: mouseLeaveHandler },
                        { type: 'mousemove', handler: mouseMoveHandler }
                    ]
                });
            } catch (error) {
                console.error(`[事件调试] 绑定事件失败 - 文件: ${fileObj.name}`, error);
            }
        });
        
        console.log(`[事件调试] 完成事件监听器设置 - 总计绑定: ${this.previewEventHandlers.length} 个文件`);
        console.log(`[事件调试] 文件列表详情:`, this.uploadedFiles.map((f, i) => `${i}: ${f.name} (${f.type})`));
    }
    
    cleanupFilePreviewListeners() {
        // 清理预览相关的事件监听器
        if (this.previewEventHandlers) {
            this.previewEventHandlers.forEach(({ element, events }) => {
                if (element && document.contains(element)) {
                    events.forEach(({ type, handler }) => {
                        try {
                            element.removeEventListener(type, handler);
                        } catch (error) {
                            console.warn('移除事件监听器失败:', error);
                        }
                    });
                }
            });
            this.previewEventHandlers = [];
        }
        
        // 隐藏预览框
        this.hideFilePreview();
        
        // 清理节流定时器
        if (this.previewState?.scrollThrottleTimer) {
            clearTimeout(this.previewState.scrollThrottleTimer);
            this.previewState.scrollThrottleTimer = null;
        }
    }
    
    // 清理所有资源（用于页面卸载时）
    cleanup() {
        // 清理预览相关
        this.cleanupFilePreviewListeners();
        
        // 清理滚动监听器
        if (this.scrollHandler) {
            window.removeEventListener('scroll', this.scrollHandler);
            this.scrollHandler = null;
        }
        
        // 清理媒体资源
        this.uploadedFiles.forEach(fileObj => {
            if (fileObj.url && fileObj.url.startsWith('blob:')) {
                URL.revokeObjectURL(fileObj.url);
            }
        });
    }
    
    // 显示需要播放的警告对话框
    showPlayingWarning() {
        const result = confirm('预览区域当前处于暂停状态，只能生成静态GIF图片。\n\n请先点击播放按钮开始预览，然后再生成动态GIF。\n\n点击"确定"开始播放，点击"取消"继续生成静态GIF。');
        
        if (result) {
            // 用户选择开始播放
            this.play();
        } else {
            // 用户选择继续生成静态GIF，直接调用generateGif但跳过播放检查
            this.generateStaticGif();
        }
    }
    
    // 生成静态GIF（跳过播放状态检查）
    async generateStaticGif() {
        if (this.uploadedFiles.length === 0) {
            alert('请先上传图片或视频');
            return;
        }
        
        const generateBtn = document.getElementById('generateBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        const wechatOptimize = document.getElementById('wechatOptimize').checked;
        
        generateBtn.disabled = true;
        generateBtn.textContent = '生成中...';
        progressContainer.style.display = 'block';
        
        try {
            const quality = parseInt(document.getElementById('gifQuality').value);
            const duration = parseFloat(document.getElementById('gifDuration').value);
            
            // 使用当前状态生成静态帧
            const frames = [];
            const canvas = document.createElement('canvas');
            canvas.width = 300;
            canvas.height = 300;
            const ctx = canvas.getContext('2d');
            
            // 只生成一帧静态图像
            this.renderToCanvas(ctx);
            const imageData = ctx.getImageData(0, 0, 300, 300);
            frames.push(imageData);
            
            progressText.textContent = '正在生成静态GIF...';
            progressFill.style.width = '50%';
            
            const originalSettings = {
                quality: quality,
                fps: 10,
                duration: duration,
                width: 300,
                height: 300
            };
            
            const gifBlob = await this.createGifFromFrames(frames, originalSettings, wechatOptimize, (progress) => {
                const percentage = 50 + (progress * 50);
                progressFill.style.width = percentage + '%';
                progressText.textContent = `生成进度: ${Math.round(percentage)}%`;
            });
            
            this.displayResult(gifBlob, originalSettings);
            
        } catch (error) {
            console.error('生成静态GIF时出错:', error);
            alert('生成失败，请重试');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = '生成GIF';
            progressContainer.style.display = 'none';
        }
    }
}

// 初始化应用 - 防止重复初始化
let generator;
if (!window.generatorInitialized) {
    document.addEventListener('DOMContentLoaded', () => {
        generator = new DynamicEmojiGenerator();
        window.generatorInitialized = true;
        console.log('✅ 动态表情包生成器已初始化');

        // 通知父窗口已就绪
        if (window.parent !== window) {
            window.parent.postMessage({ type: 'emojiGeneratorReady' }, '*');
        }
        
        // 页面卸载时清理资源
        window.addEventListener('beforeunload', () => {
            if (generator) {
                generator.cleanup();
            }
        });
        
        // 页面隐藏时隐藏预览
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && generator) {
                generator.hideFilePreview();
            }
        });
    });
}