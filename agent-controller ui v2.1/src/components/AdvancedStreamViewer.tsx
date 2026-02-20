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
  const [quality, setQuality] = useState('medium');
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
    try {
      const q = localStorage.getItem('stream:quality:screen');
      if (q) setQuality(q);
    } catch {}
  }, []);
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
  const renderFpsRef = useRef(60);
  const [preRollActive, setPreRollActive] = useState(false);
  const preRollMsRef = useRef(4000);
  const preRollStartRef = useRef(0);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioDecoderRef = useRef<any>(null);
  const opusInitializedRef = useRef<boolean>(false);
  const audioQueueRef = useRef<Float32Array[]>([]);
  const isPlayingAudioRef = useRef<boolean>(false);
  const playHeadRef = useRef<number>(0);
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
  const initAudioContext = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 44100,
        latencyHint: 'interactive'
      });
      try { audioContextRef.current.resume().catch(() => {}); } catch {}
    }
    return audioContextRef.current;
  };
  const ensureAudioDecoder = () => {
    if (audioDecoderRef.current) return audioDecoderRef.current;
    const AudioDecoderCtor = (window as any).AudioDecoder;
    if (!AudioDecoderCtor) return null;
    const audioContext = initAudioContext();
    const decoder = new AudioDecoderCtor({
      output: (audioData: any) => {
        try {
          const sampleRate = audioData.sampleRate || 48000;
          const frames = audioData.numberOfFrames || 0;
          if (!frames) return;
          const buffer = audioContext.createBuffer(audioData.numberOfChannels || 1, frames, sampleRate);
          for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
            const arr = new Float32Array(frames);
            audioData.copyTo(arr, { planeIndex: ch });
            buffer.getChannelData(ch).set(arr);
          }
          const source = audioContext.createBufferSource();
          source.buffer = buffer;
          source.connect(audioContext.destination);
          source.start();
        } catch (e) {}
      },
      error: (_e: any) => {}
    });
    try {
      decoder.configure({ codec: 'opus', sampleRate: 48000, numberOfChannels: 1 });
      opusInitializedRef.current = true;
    } catch {
      opusInitializedRef.current = false;
    }
    audioDecoderRef.current = decoder;
    return decoder;
  };
  const decodeOpusFrame = async (bytes: Uint8Array) => {
    const decoder = ensureAudioDecoder();
    if (!decoder || !opusInitializedRef.current) throw new Error('AudioDecoder not available');
    const ts = performance.now();
    const chunk = new (window as any).EncodedAudioChunk({
      type: 'key',
      timestamp: Math.floor(ts * 1000),
      data: bytes
    });
    decoder.decode(chunk);
  };
  const scheduleAudioPlayback = () => {
    const audioContext = audioContextRef.current;
    if (!audioContext) return;
    if (audioQueueRef.current.length === 0) {
      isPlayingAudioRef.current = false;
      return;
    }
    if (playHeadRef.current <= audioContext.currentTime) {
      playHeadRef.current = audioContext.currentTime + 0.05;
    }
    while (audioQueueRef.current.length) {
      const samples = audioQueueRef.current.shift();
      if (!samples) break;
      const duration = samples.length / 44100;
      const audioBuffer = audioContext.createBuffer(1, samples.length, 44100);
      const channelData = audioBuffer.getChannelData(0);
      channelData.set(samples);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      try { source.start(playHeadRef.current); } catch { source.start(); }
      playHeadRef.current += duration;
    }
    isPlayingAudioRef.current = false;
  };
  const playAudioFrame = async (payload: string | ArrayBuffer | Uint8Array) => {
    try {
      const audioContext = initAudioContext();
      try { if (audioContext.state === 'suspended') await audioContext.resume(); } catch {}
      let bytes: Uint8Array;
      if (typeof payload === 'string') {
        const binaryString = atob(payload);
        bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
      } else if (payload instanceof Uint8Array) {
        bytes = payload;
      } else if (payload instanceof ArrayBuffer) {
        bytes = new Uint8Array(payload);
      } else {
        return;
      }
      const isLikelyPCM16 = bytes.length % 2 === 0;
      const canUseWebCodecs = typeof (window as any).AudioDecoder !== 'undefined';
      if (!isLikelyPCM16 && canUseWebCodecs) {
        try { await decodeOpusFrame(bytes); return; } catch {}
      }
      const samples16 = new Int16Array(bytes.buffer, bytes.byteOffset, Math.floor(bytes.byteLength / 2));
      const floatSamples = new Float32Array(samples16.length);
      for (let i = 0; i < samples16.length; i++) floatSamples[i] = samples16[i] / 32768.0;
      audioQueueRef.current.push(floatSamples);
      if (!isPlayingAudioRef.current) {
        const prerollBuffers = 2;
        if (audioQueueRef.current.length < prerollBuffers) {
          setTimeout(() => {
            if (!isPlayingAudioRef.current) {
              isPlayingAudioRef.current = true;
              scheduleAudioPlayback();
            }
          }, 20);
        } else {
          isPlayingAudioRef.current = true;
          scheduleAudioPlayback();
        }
      }
    } catch {}
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
      const cap = Math.max(30, Math.floor((preRollMsRef.current / 1000) * renderFpsRef.current) * 2);
      if (queue.length > cap) queue.splice(cap);
      const now = Date.now();
      if (preRollActive) {
        const oldest = queue[0];
        if (!oldest) return;
        const age = now - oldest.receivedAt;
        if (age < preRollMsRef.current) return;
        setPreRollActive(false);
      }
      let item: { frame: any; receivedAt: number } | null = null;
      while (queue.length) {
        const age = now - queue[0].receivedAt;
        if (age >= preRollMsRef.current) {
          item = queue.shift() as any;
        } else {
          break;
        }
      }
      if (!item) {
        item = queue.pop() as any;
        if (!item) return;
      }
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
    if (!isStreaming) return;
    const onAudio = (event: any) => {
      const data = event.detail;
      if (data.agent_id !== agentId) return;
      try { playAudioFrame(data.frame); } catch {}
    };
    window.addEventListener('audio_frame', onAudio);
    return () => { window.removeEventListener('audio_frame', onAudio); };
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
    const fps = (quality === 'low' ? 30 : quality === 'medium' ? 50 : quality === 'high' ? 60 : 60);
    const buf = (quality === 'low' ? 200 : quality === 'medium' ? 260 : quality === 'high' ? 300 : 360);
    socket.emit('set_stream_mode', { agent_id: agentId, type: 'screen', mode: 'buffered', fps, buffer_frames: buf });
    const res = await apiClient.startStream(agentId, 'screen', quality, 'buffered', fps, buf);
    if (!res?.success) {
      const msg = (res?.error || (res?.data as any)?.error || (res?.data as any)?.message || 'Failed to start stream');
      try { (window as any).toast?.error?.(String(msg)); } catch {}
      return;
    }
    setIsStreaming(true);
    socket.emit('get_monitors', { agent_id: agentId });
    // Apply current cursor emission preference after stream starts
    applyCursorEmit(agentCursorEmit);
    try { socket.emit('set_stream_params', { type: 'screen', fps }); } catch {}
    try { renderFpsRef.current = Math.min(fps, 60); } catch {}
    preRollMsRef.current = (quality === 'low' ? 7000 : quality === 'medium' ? 9000 : quality === 'high' ? 11000 : 12000);
    preRollStartRef.current = Date.now();
    setPreRollActive(true);
    frameQueueRef.current = [];
  };
  const stopStream = async () => {
    if (!socket) return;
    try { await apiClient.stopStream(agentId, 'screen'); } catch {}
    setIsStreaming(false);
  };
  const changeQuality = async (q: string) => {
    setQuality(q);
    try { localStorage.setItem('stream:quality:screen', q); } catch {}
    const fps = (q === 'low' ? 30 : q === 'medium' ? 50 : q === 'high' ? 60 : 60);
    try { if (socket) socket.emit('set_stream_params', { type: 'screen', fps }); } catch {}
    try { renderFpsRef.current = Math.min(fps, 60); } catch {}
    preRollMsRef.current = (q === 'low' ? 7000 : q === 'medium' ? 9000 : q === 'high' ? 11000 : 12000);
    if (isStreaming) {
      await stopStream();
      await startStream();
    }
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
        {isStreaming && preRollActive && (
          <div className="stream-overlay">
            Capturing frames…
          </div>
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
