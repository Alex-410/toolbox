// 摄像头选择器共享模块
// 用法: 在 HTML 中 <script type="module"> 内 import { initCameraSelector, getSelectedStream } from './camera-selector.js';

const VIRTUAL_KEYWORDS = ['virtual', 'obs', 'smart connect', '爱思', 'droidcam', 'iriun', 'ip webcam', 'screen', 'display'];

let allCameras = [];
let selectedDeviceId = null;
let userManuallySelected = false;

/**
 * 初始化摄像头选择器 UI
 * @param {HTMLElement} container - 放置选择器的容器元素
 * @param {Function} onChange - 切换摄像头时的回调
 */
export async function initCameraSelector(container, onChange) {
    if (!container) {
        console.warn('camera-selector: container 不存在');
        return;
    }

    // 创建 UI
    container.innerHTML = `
        <div class="setting-group">
            <label>摄像头选择</label>
            <select id="cameraSelect_${Date.now()}" style="width:100%;background:#1e1e1e;border:1px solid #333;border-radius:6px;color:#e0e0e0;padding:6px;font-size:13px;">
                <option value="">点击"开启摄像头"后显示列表</option>
            </select>
        </div>
    `;

    const select = container.querySelector('select');

    // 先尝试枚举设备（不需要权限就能拿到部分信息）
    try {
        await refreshCameraList(select);
    } catch (e) {
        console.warn('初始枚举设备失败:', e);
    }

    select.addEventListener('change', async () => {
        selectedDeviceId = select.value;
        userManuallySelected = true;
        console.log('切换摄像头:', selectedDeviceId);
        if (onChange) {
            try {
                await onChange(selectedDeviceId);
            } catch (e) {
                console.error('切换摄像头回调错误:', e);
            }
        }
    });

    // 监听设备变化
    if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
        navigator.mediaDevices.addEventListener('devicechange', () => refreshCameraList(select));
    }
}

/**
 * 刷新摄像头列表
 */
async function refreshCameraList(select) {
    const devices = await navigator.mediaDevices.enumerateDevices();
    allCameras = devices.filter(d => d.kind === 'videoinput');

    select.innerHTML = '';

    if (allCameras.length === 0) {
        select.innerHTML = '<option value="">未检测到摄像头</option>';
        return;
    }

    const hasLabels = allCameras.some(cam => cam.label && cam.label.length > 0);

    const physical = [];
    const virtual = [];
    const unlabeled = [];

    allCameras.forEach(cam => {
        const label = cam.label || '';
        const lower = label.toLowerCase();
        if (!label) {
            unlabeled.push(cam);
        } else if (VIRTUAL_KEYWORDS.some(k => lower.includes(k))) {
            virtual.push(cam);
        } else {
            physical.push(cam);
        }
    });

    if (physical.length > 0) {
        const group = document.createElement('optgroup');
        group.label = '实体摄像头';
        physical.forEach((cam, i) => {
            const opt = document.createElement('option');
            opt.value = cam.deviceId;
            opt.textContent = cam.label || `摄像头 ${i + 1}`;
            group.appendChild(opt);
        });
        select.appendChild(group);
    }

    if (virtual.length > 0) {
        const group = document.createElement('optgroup');
        group.label = '虚拟摄像头';
        virtual.forEach((cam, i) => {
            const opt = document.createElement('option');
            opt.value = cam.deviceId;
            opt.textContent = cam.label || `虚拟摄像头 ${i + 1}`;
            group.appendChild(opt);
        });
        select.appendChild(group);
    }

    if (unlabeled.length > 0) {
        const group = document.createElement('optgroup');
        group.label = '其他摄像头';
        unlabeled.forEach((cam, i) => {
            const opt = document.createElement('option');
            opt.value = cam.deviceId;
            opt.textContent = `摄像头 ${i + 1}`;
            group.appendChild(opt);
        });
        select.appendChild(group);
    }

    if (!userManuallySelected) {
        if (physical.length > 0) {
            selectedDeviceId = physical[0].deviceId;
        } else if (allCameras.length > 0) {
            selectedDeviceId = allCameras[0].deviceId;
        }
    } else if (hasLabels) {
        const currentIsVirtual = virtual.some(cam => cam.deviceId === selectedDeviceId);
        if (currentIsVirtual && physical.length > 0) {
            selectedDeviceId = physical[0].deviceId;
        }
    }

    if (selectedDeviceId) {
        select.value = selectedDeviceId;
    }
}

/**
 * 获取选中摄像头的 MediaStream
 * @param {object} constraints - 额外约束 (如 width, height)
 * @returns {Promise<MediaStream>}
 */
export async function getSelectedStream(constraints = {}) {
    const labelsKnown = allCameras.some(cam => cam.label && cam.label.length > 0);

    if (!labelsKnown) {
        const tempStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
            audio: false
        });
        tempStream.getTracks().forEach(t => t.stop());

        const select = document.querySelector('select[id^="cameraSelect"]');
        if (select) await refreshCameraList(select);
    }

    const videoConstraints = selectedDeviceId
        ? { deviceId: { exact: selectedDeviceId } }
        : { facingMode: 'user' };

    const finalConstraints = {
        video: { ...videoConstraints, width: { ideal: 1280 }, height: { ideal: 720 }, ...constraints },
        audio: false
    };

    const stream = await navigator.mediaDevices.getUserMedia(finalConstraints);

    setTimeout(() => {
        const select = document.querySelector('select[id^="cameraSelect"]');
        if (select) refreshCameraList(select);
    }, 500);

    return stream;
}

/**
 * 获取当前选中的设备 ID
 */
export function getSelectedDeviceId() {
    return selectedDeviceId;
}

/**
 * 获取所有摄像头列表
 */
export function getAllCameras() {
    return allCameras;
}
