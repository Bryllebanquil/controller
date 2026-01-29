import React, { useEffect, useRef, useState } from 'react';
import { useSocket } from './SocketProvider';
type Monitor = { index: number; width: number; height: number; left: number; top: number; name: string; primary: boolean };
type StreamStats = { fps: number; quality: string; bandwidth_mbps: number; avg_frame_time: number };
export function AdvancedStreamViewer({ agentId, useWebRTC = true }: { agentId: string; useWebRTC?: boolean }) {
  const { socket } = useSocket();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
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
    if (!useWebRTC || !socket) return;
    const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }, { urls: 'stun:stun1.l.google.com:19302' }] });
    pcRef.current = pc;
    pc.ontrack = e => {
      if (e.track.kind === 'video' && videoRef.current) {
        const stream = new MediaStream([e.track]);
        videoRef.current.srcObject = stream;
      }
    };
    pc.onicecandidate = e => {
      if (e.candidate && socket) {
        socket.emit('webrtc_ice_candidate', { agent_id: agentId, candidate: e.candidate });
      }
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === 'failed') {
        stopStream();
        setTimeout(() => startStream(), 2000);
      }
    };
    return () => {
      pc.close();
    };
  }, [socket, agentId, useWebRTC]);
  useEffect(() => {
    if (!socket) return;
    const onOffer = async (data: any) => {
      if (data.agent_id !== agentId || !pcRef.current) return;
      try {
        await pcRef.current.setRemoteDescription({ type: 'offer', sdp: data.offer });
        const answer = await pcRef.current.createAnswer();
        await pcRef.current.setLocalDescription(answer);
        socket.emit('webrtc_answer', { agent_id: agentId, answer: answer.sdp });
      } catch {}
    };
    const onIce = async (data: any) => {
      if (data.agent_id !== agentId || !pcRef.current) return;
      try {
        await pcRef.current.addIceCandidate(new RTCIceCandidate(data.candidate));
      } catch {}
    };
    const onMonitors = (data: any) => {
      if (data.agent_id === agentId) setMonitors(Array.isArray(data.monitors) ? data.monitors : []);
    };
    const onStats = (data: any) => {
      if (data.agent_id === agentId && data.stats?.screen) setStats(data.stats.screen);
    };
    socket.on('webrtc_offer', onOffer);
    socket.on('webrtc_ice_candidate', onIce);
    socket.on('monitors_list_update', onMonitors);
    socket.on('stream_stats_update', onStats);
    return () => {
      socket.off('webrtc_offer', onOffer);
      socket.off('webrtc_ice_candidate', onIce);
      socket.off('monitors_list_update', onMonitors);
      socket.off('stream_stats_update', onStats);
    };
  }, [socket, agentId]);
  const startStream = () => {
    if (!socket) return;
    if (useWebRTC) {
      socket.emit('start_webrtc_streaming', { agent_id: agentId, type: 'all', quality, fps: quality === 'ultra' ? 60 : 30 });
    } else {
      socket.emit('start_stream', { agent_id: agentId, type: 'screen', quality });
    }
    setIsStreaming(true);
    socket.emit('get_monitors', { agent_id: agentId });
  };
  const stopStream = () => {
    if (!socket) return;
    if (useWebRTC) {
      socket.emit('stop_webrtc_streaming', { agent_id: agentId });
    } else {
      socket.emit('stop_stream', { agent_id: agentId, type: 'screen' });
    }
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
        {useWebRTC ? <video ref={videoRef} autoPlay playsInline muted={false} className="stream-video" /> : <canvas ref={canvasRef} className="stream-canvas" />}
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
