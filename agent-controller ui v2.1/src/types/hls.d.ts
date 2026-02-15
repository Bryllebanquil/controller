declare module 'hls.js' {
  export default class Hls {
    static isSupported(): boolean;
    constructor(config?: any);
    loadSource(url: string): void;
    attachMedia(media: HTMLVideoElement): void;
    destroy(): void;
    on(event: string, handler: (...args: any[]) => void): void;
    off(event: string, handler: (...args: any[]) => void): void;
  }
}
