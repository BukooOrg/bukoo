export class TexturePreloader {
  static instance;
  preloadedTextures = new Map();
  loadingPromises = new Map();

  static getInstance() {
    if (!TexturePreloader.instance) {
      TexturePreloader.instance = new TexturePreloader();
    }
    return TexturePreloader.instance;
  }

  async preloadImage(url) {
    if (!url) return null;
    if (this.preloadedTextures.has(url)) {
      return this.preloadedTextures.get(url);
    }

    if (this.loadingPromises.has(url)) {
      return this.loadingPromises.get(url);
    }

    const loadPromise = new Promise((resolve, reject) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        this.preloadedTextures.set(url, img);
        this.loadingPromises.delete(url);
        resolve(img);
      };
      img.onerror = () => {
        this.loadingPromises.delete(url);
        reject(new Error(`Failed to preload image: ${url}`));
      };
      img.src = url;
    });

    this.loadingPromises.set(url, loadPromise);
    return loadPromise;
  }

  getPreloadedImage(url) {
    return this.preloadedTextures.get(url) || null;
  }
}
