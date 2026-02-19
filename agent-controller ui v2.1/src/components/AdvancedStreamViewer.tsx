import React, { useEffect, useRef, useState } from 'react';
import { useSocket } from './SocketProvider';
import apiClient from '../services/api';
type Monitor = { index: number; width: number; height: number; left: number; top: number; name: string; primary: boolean };
type StreamStats = { fps: number; quality: string; bandwidth_mbps: number; avg_frame_time: number };
export function AdvancedStreamViewer({ agentId }: { agentId: string }) {
  const { socket } = useSocket();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [remoteCursor, setRemoteCursor] = useState<{ x: number; y: number; visible: boolean } | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showRemoteCursor, setShowRemoteCursor] = useState(true);
  const [agentCursorEmit, setAgentCursorEmit] = useState(true);
  const [quality, setQuality] = useState('high');
  const [stats, setStats] = useState<StreamStats | null>(null);
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [currentMonitor, setCurrentMonitor] = useState(1);
  const [displayMode, setDisplayMode] = useState<'single' | 'combined' | 'pip'>('single');
  const [pipMonitor, setPipMonitor] = useState(2);
  const [micVolume, setMicVolume] = useState(1.0);
  const [systemVolume, setSystemVolume] = useState(1.0);
  const [noiseReduction, setNoiseReduction] = useState(false);
  const [echoCancellation, setEchoCancellation] = useState(false);
  useEffect(() => {
    if (!socket) return;
    const onMonitors = (data: any) => {
      if (data.agent_id === agentId) setMonitors(Array.isArray(data.monitors) ? data.monitors : []);
    };
    const onStats = (data: any) => {
      if (data.agent_id === agentId && data.stats?.screen) setStats(data.stats.screen);
    };
    socket.on('monitors_list_update', onMonitors);
    socket.on('stream_stats_update', onStats);
    return () => {
      socket.off('monitors_list_update', onMonitors);
      socket.off('stream_stats_update', onStats);
    };
  }, [socket, agentId]);
  useEffect(() => {
    const onCursor = (event: any) => {
      const d = event.detail || {};
      if (String(d.agent_id || '') !== String(agentId || '')) return;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const sw = Number(d.screen_w || 0);
      const sh = Number(d.screen_h || 0);
      if (!sw || !sh) return;
      const x = Math.round((Number(d.x || 0) / sw) * canvas.width);
      const y = Math.round((Number(d.y || 0) / sh) * canvas.height);
      setRemoteCursor({ x, y, visible: Boolean(d.visible !== false) });
    };
    window.addEventListener('cursor_update', onCursor);
    return () => {
      window.removeEventListener('cursor_update', onCursor);
    };
  }, [agentId]);
  const frameQueueRef = useRef<{ frame: string | Uint8Array; receivedAt: number }[]>([]);
  const renderLoopRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const renderFpsRef = useRef(20);
  const latestBaselineRef = useRef<number>(0);
  const applyCursorEmit = (enabled: boolean) => {
    if (!socket) return;
    socket.emit('set_stream_params', { type: 'screen', cursor_emit: enabled });
  };
  const normalizeFramePayload = (payload: any): string | Uint8Array | null => {
    if (typeof payload === 'string') {
      const s = payload.startsWith('data:') ? payload.split(',')[1] || '' : payload;
      return s || null;
    }
    if (payload instanceof Uint8Array) return payload;
    if (payload instanceof ArrayBuffer) return new Uint8Array(payload);
    if (payload && typeof payload === 'object' && 'byteLength' in payload) {
      return new Uint8Array(payload as ArrayBuffer);
    }
    return null;
  };
  const drawFrameToCanvas = (payload: string | Uint8Array) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let blob: Blob | null = null;
    if (typeof payload === 'string') {
      if (!payload) return;
      const binary = atob(payload);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      blob = new Blob([bytes], { type: 'image/jpeg' });
    } else {
      const view = payload instanceof Uint8Array ? payload : new Uint8Array(payload);
      const copy = new Uint8Array(view.byteLength);
      copy.set(view);
      blob = new Blob([copy.buffer], { type: 'image/jpeg' });
    }
    if (!blob) return;
    createImageBitmap(blob).then((bitmap) => {
      if (!canvas) return;
      if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
      }
      const ctx = canvas.getContext('2d');
      if (ctx) ctx.drawImage(bitmap, 0, 0);
    }).catch(() => {});
  };
  const drawTileToCanvas = (x: number, y: number, w: number, h: number, payload: string | Uint8Array) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let blob: Blob | null = null;
    if (typeof payload === 'string') {
      if (!payload) return;
      const binary = atob(payload);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      blob = new Blob([bytes], { type: 'image/jpeg' });
    } else {
      const view = payload instanceof Uint8Array ? payload : new Uint8Array(payload);
      const copy = new Uint8Array(view.byteLength);
      copy.set(view);
      blob = new Blob([copy.buffer], { type: 'image/jpeg' });
    }
    if (!blob) return;
    createImageBitmap(blob).then((bitmap) => {
      const ctx = canvas?.getContext('2d');
      if (!ctx || !canvas) return;
      const dw = w || bitmap.width;
      const dh = h || bitmap.height;
      ctx.drawImage(bitmap, x, y, dw, dh);
    }).catch(() => {});
  };
  useEffect(() => {
    if (!isStreaming || !agentId) return;
    const handleFrame = (event: any) => {
      const data = event.detail;
      if (data.agent_id !== agentId) return;
      const normalized = normalizeFramePayload(data.frame);
      if (normalized) {
        const queue = frameQueueRef.current;
        queue.push({ frame: normalized, receivedAt: Date.now() });
      }
    };
    window.addEventListener('screen_frame', handleFrame);
    return () => {
      window.removeEventListener('screen_frame', handleFrame);
    };
  }, [isStreaming, agentId]);
  useEffect(() => {
    if (!isStreaming || !agentId) return;
    const onKeyframe = (event: any) => {
      const data = event.detail || {};
      if (data.agent_id !== agentId) return;
      const fid = Number(data.frame_id || 0);
      if (Number.isFinite(fid) && fid > 0) latestBaselineRef.current = fid;
      const normalized = normalizeFramePayload(data.frame);
      if (normalized) {
        const canvas = canvasRef.current;
        if (canvas && typeof data.width === 'number' && typeof data.height === 'number') {
          canvas.width = data.width;
          canvas.height = data.height;
        }
        drawFrameToCanvas(normalized);
      }
    };
    const onTile = (event: any) => {
      const data = event.detail || {};
      if (data.agent_id !== agentId) return;
      const fid = Number(data.frame_id || 0);
      if (!latestBaselineRef.current || (Number.isFinite(fid) && fid < latestBaselineRef.current)) return;
      const normalized = normalizeFramePayload(data.frame);
      if (!normalized) return;
      const x = Number(data.x || 0);
      const y = Number(data.y || 0);
      const w = Number(data.w || 0);
      const h = Number(data.h || 0);
      drawTileToCanvas(x, y, w, h, normalized);
    };
    window.addEventListener('screen_keyframe', onKeyframe);
    window.addEventListener('screen_tile', onTile);
    return () => {
      window.removeEventListener('screen_keyframe', onKeyframe);
      window.removeEventListener('screen_tile', onTile);
    };
  }, [isStreaming, agentId]);
  useEffect(() => {
    if (!isStreaming || !agentId) return;
    const intervalMs = Math.max(10, Math.floor(1000 / Math.max(1, renderFpsRef.current)));
    if (renderLoopRef.current) {
      clearInterval(renderLoopRef.current);
      renderLoopRef.current = null;
    }
    renderLoopRef.current = setInterval(() => {
      const queue = frameQueueRef.current;
      if (!queue.length) return;
      const maxQueue = 6;
      if (queue.length > maxQueue) queue.splice(0, queue.length - maxQueue);
      const item = queue.shift();
      if (!item) return;
      drawFrameToCanvas(item.frame);
    }, intervalMs);
    return () => {
      if (renderLoopRef.current) {
        clearInterval(renderLoopRef.current);
        renderLoopRef.current = null;
      }
      frameQueueRef.current = [];
    };
  }, [isStreaming, agentId]);
  useEffect(() => {
    if (!socket || !isStreaming || !agentId) return;
    const req = () => {
      socket.emit('request_video_frame', { agent_id: agentId });
    };
    req();
    const timeout = window.setTimeout(() => {
      req();
    }, 1200);
    return () => {
      window.clearTimeout(timeout);
    };
  }, [socket, isStreaming, agentId]);
  const startStream = async () => {
    if (!socket) return;
    socket.emit('set_stream_mode', { agent_id: agentId, type: 'screen', mode: 'buffered', fps: 5, buffer_frames: 10 });
    const res = await apiClient.startStream(agentId, 'screen', quality, 'buffered', 5, 10);
    if (!res?.success) {
      const msg = (res?.error || (res?.data as any)?.error || (res?.data as any)?.message || 'Failed to start stream');
      try { (window as any).toast?.error?.(String(msg)); } catch {}
      return;
    }
    setIsStreaming(true);
    socket.emit('get_monitors', { agent_id: agentId });
    // Apply current cursor emission preference after stream starts
    applyCursorEmit(agentCursorEmit);
  };
  const stopStream = async () => {
    if (!socket) return;
    try { await apiClient.stopStream(agentId, 'screen'); } catch {}
    setIsStreaming(false);
  };
  const changeQuality = (q: string) => {
    setQuality(q);
    if (socket) socket.emit('set_stream_quality', { agent_id: agentId, quality: q });
  };
  const switchMonitor = (m: number) => {
    setCurrentMonitor(m);
    if (socket) socket.emit('switch_monitor', { agent_id: agentId, monitor_index: m });
  };
  const changeDisplayMode = (m: 'single' | 'combined' | 'pip') => {
    setDisplayMode(m);
    if (socket) socket.emit('set_display_mode', { agent_id: agentId, mode: m, pip_monitor: m === 'pip' ? pipMonitor : undefined });
  };
  const updateAudioVolumes = () => {
    if (socket) socket.emit('set_audio_volumes', { agent_id: agentId, mic_volume: micVolume, system_volume: systemVolume });
  };
  const toggleNoiseReduction = () => {
    const v = !noiseReduction;
    setNoiseReduction(v);
    if (socket) socket.emit('toggle_noise_reduction', { agent_id: agentId, enabled: v });
  };
  const toggleEchoCancellation = () => {
    const v = !echoCancellation;
    setEchoCancellation(v);
    if (socket) socket.emit('toggle_echo_cancellation', { agent_id: agentId, enabled: v });
  };
  return (
    <div className="advanced-stream-viewer">
      <div className="stream-controls">
        <div className="control-group">
          <button onClick={isStreaming ? stopStream : startStream}>{isStreaming ? 'Stop Stream' : 'Start Stream'}</button>
          <select value={quality} onChange={e => changeQuality(e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="ultra">Ultra</option>
          </select>
        </div>
        {monitors.length > 1 && (
          <div className="control-group">
            <label>Monitor</label>
            <select value={currentMonitor} onChange={e => switchMonitor(parseInt(e.target.value))}>
              {monitors.map(m => (
                <option key={m.index} value={m.index}>{m.name}</option>
              ))}
            </select>
          </div>
        )}
        {monitors.length > 1 && (
          <div className="control-group">
            <label>Display Mode</label>
            <select value={displayMode} onChange={e => changeDisplayMode(e.target.value as any)}>
              <option value="single">Single</option>
              <option value="combined">Combined</option>
              <option value="pip">Picture-in-Picture</option>
            </select>
            {displayMode === 'pip' && (
              <select value={pipMonitor} onChange={e => setPipMonitor(parseInt(e.target.value))}>
                {monitors.map(m => (
                  <option key={m.index} value={m.index}>PIP {m.name}</option>
                ))}
              </select>
            )}
          </div>
        )}
        <div className="control-group">
          <label>Mic Volume</label>
          <input type="range" min="0" max="1" step="0.1" value={micVolume} onChange={e => { setMicVolume(parseFloat(e.target.value)); updateAudioVolumes(); }} />
          <label>System Volume</label>
          <input type="range" min="0" max="1" step="0.1" value={systemVolume} onChange={e => { setSystemVolume(parseFloat(e.target.value)); updateAudioVolumes(); }} />
          <button onClick={toggleNoiseReduction}>{noiseReduction ? 'Noise Reduction On' : 'Noise Reduction Off'}</button>
          <button onClick={toggleEchoCancellation}>{echoCancellation ? 'Echo Cancel On' : 'Echo Cancel Off'}</button>
        </div>
      </div>
      <div className="stream-display">
        <canvas ref={canvasRef} className="stream-canvas" />
        {showRemoteCursor && remoteCursor?.visible && (
          <div
            className="absolute"
            style={{
              left: `${remoteCursor.x}px`,
              top: `${remoteCursor.y}px`,
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: '#ffffff',
              border: '1px solid #000000',
              transform: 'translate(-50%, -50%)',
              pointerEvents: 'none'
            }}
          />
        )}
      </div>
      <div className="control-group mt-2">
        <label style={{ marginRight: 8 }}>
          <input
            type="checkbox"
            checked={showRemoteCursor}
            onChange={(e) => setShowRemoteCursor(e.target.checked)}
          /> Show remote cursor overlay
        </label>
        <label style={{ marginLeft: 12 }}>
          <input
            type="checkbox"
            checked={agentCursorEmit}
            onChange={(e) => {
              const v = e.target.checked;
              setAgentCursorEmit(v);
              applyCursorEmit(v);
            }}
          /> Agent cursor events
        </label>
      </div>
      {stats && (
        <div className="stream-stats">
          <div className="stat"><span className="label">FPS</span><span className="value">{stats.fps}</span></div>
          <div className="stat"><span className="label">Quality</span><span className="value">{stats.quality}</span></div>
          <div className="stat"><span className="label">Bandwidth</span><span className="value">{stats.bandwidth_mbps.toFixed(2)} Mbps</span></div>
          <div className="stat"><span className="label">Latency</span><span className="value">{stats.avg_frame_time.toFixed(1)} ms</span></div>
        </div>
      )}
    </div>
  );
}
