import React, { useEffect, useRef, useState } from 'react';

type CursorEvt = { x: number; y: number; screen_w: number; screen_h: number; visible: boolean; ts: number; agent_id: string };

export function FrameBuilderTest({ agentId }: { agentId: string | null }) {
  const [active, setActive] = useState(false);
  const [delayMs, setDelayMs] = useState(12);
  const [overlayEnabled, setOverlayEnabled] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const offscreenRef = useRef<HTMLCanvasElement | null>(null);
  const latestBaselineRef = useRef<number>(0);
  const lastPresentedRef = useRef<number>(0);
  const scheduledRef = useRef<Map<number, number>>(new Map());
  const cursorEventsRef = useRef<CursorEvt[]>([]);
  const remoteCursorRef = useRef<{ x: number; y: number; visible: boolean } | null>(null);
  const [, forceRender] = useState(0);

  const normalize = (payload: any): string | Uint8Array | null => {
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

  const toBlob = (payload: string | Uint8Array): Blob | null => {
    if (typeof payload === 'string') {
      if (!payload) return null;
      const binary = atob(payload);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      return new Blob([bytes], { type: 'image/jpeg' });
    }
    const view = payload instanceof Uint8Array ? payload : new Uint8Array(payload);
    const copy = new Uint8Array(view.byteLength);
    copy.set(view);
    return new Blob([copy.buffer], { type: 'image/jpeg' });
  };

  const ensureOffscreen = (w: number, h: number) => {
    if (!offscreenRef.current) offscreenRef.current = document.createElement('canvas');
    const off = offscreenRef.current!;
    if (off.width !== w || off.height !== h) {
      off.width = w;
      off.height = h;
    }
    return off;
  };

  const commitFrame = (fid: number) => {
    const canvas = canvasRef.current;
    const off = offscreenRef.current;
    if (!canvas || !off) return;
    if (fid < latestBaselineRef.current) return;
    if (fid < lastPresentedRef.current) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    if (canvas.width !== off.width || canvas.height !== off.height) {
      canvas.width = off.width;
      canvas.height = off.height;
    }
    ctx.drawImage(off, 0, 0);
    lastPresentedRef.current = fid;
    const now = performance.now();
    let best: CursorEvt | null = null;
    const evts = cursorEventsRef.current;
    for (let i = evts.length - 1; i >= 0; i--) {
      const e = evts[i];
      if (e.agent_id !== String(agentId || '')) continue;
      if (!best || Math.abs(now - e.ts) < Math.abs(now - best.ts)) best = e;
      if (e.ts <= now) break;
    }
    if (overlayEnabled && best && canvas) {
      const x = Math.round((best.x / Math.max(1, best.screen_w)) * canvas.width);
      const y = Math.round((best.y / Math.max(1, best.screen_h)) * canvas.height);
      remoteCursorRef.current = { x, y, visible: best.visible !== false };
      forceRender(v => v + 1);
    }
  };

  const scheduleCommit = (fid: number) => {
    const existing = scheduledRef.current.get(fid);
    if (existing) {
      window.clearTimeout(existing);
      scheduledRef.current.delete(fid);
    }
    const id = window.setTimeout(() => {
      scheduledRef.current.delete(fid);
      commitFrame(fid);
    }, Math.max(0, delayMs));
    scheduledRef.current.set(fid, id);
  };

  useEffect(() => {
    if (!active || !agentId) return;
    const onCursor = (event: any) => {
      const d = event.detail || {};
      const e: CursorEvt = {
        x: Number(d.x || 0),
        y: Number(d.y || 0),
        screen_w: Number(d.screen_w || 0),
        screen_h: Number(d.screen_h || 0),
        visible: Boolean(d.visible !== false),
        ts: performance.now(),
        agent_id: String(d.agent_id || '')
      };
      cursorEventsRef.current.push(e);
      if (cursorEventsRef.current.length > 200) cursorEventsRef.current.splice(0, cursorEventsRef.current.length - 200);
    };
    const onKeyframe = (event: any) => {
      const data = event.detail || {};
      if (String(data.agent_id || '') !== String(agentId || '')) return;
      const fid = Number(data.frame_id || 0);
      if (Number.isFinite(fid) && fid > 0) latestBaselineRef.current = fid;
      const payload = normalize(data.frame);
      if (!payload) return;
      const blob = toBlob(payload);
      if (!blob) return;
      createImageBitmap(blob).then((bitmap) => {
        const off = ensureOffscreen(bitmap.width, bitmap.height);
        const ctx = off.getContext('2d');
        if (!ctx) return;
        ctx.drawImage(bitmap, 0, 0);
        scheduleCommit(fid || latestBaselineRef.current || 0);
      }).catch(() => {});
    };
    const onTile = (event: any) => {
      const data = event.detail || {};
      if (String(data.agent_id || '') !== String(agentId || '')) return;
      const fid = Number(data.frame_id || 0);
      if (!latestBaselineRef.current || (Number.isFinite(fid) && fid < latestBaselineRef.current)) return;
      const payload = normalize(data.frame);
      if (!payload) return;
      const x = Number(data.x || 0);
      const y = Number(data.y || 0);
      const w = Number(data.w || 0);
      const h = Number(data.h || 0);
      const blob = toBlob(payload);
      if (!blob) return;
      createImageBitmap(blob).then((bitmap) => {
        const off = offscreenRef.current;
        if (!off) return;
        const ctx = off.getContext('2d');
        if (!ctx) return;
        const dw = w || bitmap.width;
        const dh = h || bitmap.height;
        ctx.drawImage(bitmap, x, y, dw, dh);
        scheduleCommit(fid || latestBaselineRef.current || 0);
      }).catch(() => {});
    };
    window.addEventListener('cursor_update', onCursor);
    window.addEventListener('screen_keyframe', onKeyframe);
    window.addEventListener('screen_tile', onTile);
    return () => {
      window.removeEventListener('cursor_update', onCursor);
      window.removeEventListener('screen_keyframe', onKeyframe);
      window.removeEventListener('screen_tile', onTile);
      scheduledRef.current.forEach((id) => window.clearTimeout(id));
      scheduledRef.current.clear();
      offscreenRef.current = null;
      remoteCursorRef.current = null;
      latestBaselineRef.current = 0;
      lastPresentedRef.current = 0;
      cursorEventsRef.current = [];
    };
  }, [active, agentId, delayMs, overlayEnabled]);

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <button
          className="px-3 py-1 rounded bg-blue-600 text-white text-xs"
          onClick={() => setActive(v => !v)}
          disabled={!agentId}
        >
          {active ? 'Stop Test' : 'Start Test'}
        </button>
        <label className="text-xs">Delay</label>
        <input
          type="number"
          className="w-16 border rounded px-1 py-0.5 text-xs"
          value={delayMs}
          onChange={(e) => setDelayMs(Math.max(0, Math.min(50, Number(e.target.value || 0))))}
        />
        <label className="text-xs flex items-center space-x-1">
          <input
            type="checkbox"
            checked={overlayEnabled}
            onChange={(e) => setOverlayEnabled(e.target.checked)}
          />
          <span>Cursor Overlay</span>
        </label>
      </div>
      <div className="relative aspect-video bg-black rounded overflow-hidden">
        <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
        {overlayEnabled && remoteCursorRef.current && remoteCursorRef.current.visible && (
          <div
            className="absolute"
            style={{
              left: `${remoteCursorRef.current.x}px`,
              top: `${remoteCursorRef.current.y}px`,
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
    </div>
  );
}
