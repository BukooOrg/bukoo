import React, { useState, useRef, useEffect } from 'react';

import { BookModel } from './book-canvas';

export function BookViewer3D({ frontCoverUrl, backCoverUrl }) {
  const [bookReady, setBookReady] = useState(false);
  const [hasInitialAnimationPlayed, setHasInitialAnimationPlayed] = useState(false);
  const [screenWidth, setScreenWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1200
  );
  const [screenHeight, setScreenHeight] = useState(
    typeof window !== 'undefined' ? window.innerHeight : 800
  );
  const meshRef = useRef(null);

  const getResponsiveFOV = (width, height) => {
    const aspectRatio = width / height;
    if (width < 1024) return aspectRatio < 1 ? 26 : 28;
    if (width <= 1200) return aspectRatio < 1.3 ? 48 : 30;
    return aspectRatio < 1.3 ? 44 : 30;
  };

  const initialParams = {
    scale: [5, 5, 5],
    position: [-3, -3, -3],
    rotation: [1.6, 0.0, 0.3],
    cameraPosition: [-4.1, -3.3, 0.2],
    cameraFov: getResponsiveFOV(screenWidth, screenHeight),
  };

  const defaultParams = {
    scale: [5, 5, 5],
    position: [-3, -3, -3],
    rotation: [1.2, 0, 0],
    cameraPosition: [-4.2, -2.9, 0.4],
    cameraFov: getResponsiveFOV(screenWidth, screenHeight),
  };

  const [params, setParams] = useState(initialParams);

  useEffect(() => {
    const handleResize = () => {
      setScreenWidth(window.innerWidth);
      setScreenHeight(window.innerHeight);
      setParams((prev) => ({
        ...prev,
        cameraFov: getResponsiveFOV(window.innerWidth, window.innerHeight),
      }));
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (bookReady && !hasInitialAnimationPlayed) {
      const startTime = Date.now();
      const duration = 1500;

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = (t) => (t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1);
        const easedProgress = ease(progress);

        setParams((prev) => ({
          ...prev,
          rotation: [
            initialParams.rotation[0] +
              (defaultParams.rotation[0] - initialParams.rotation[0]) * easedProgress,
            initialParams.rotation[1] +
              (defaultParams.rotation[1] - initialParams.rotation[1]) * easedProgress,
            initialParams.rotation[2] +
              (defaultParams.rotation[2] - initialParams.rotation[2]) * easedProgress,
          ],
          cameraFov:
            initialParams.cameraFov +
            (defaultParams.cameraFov - initialParams.cameraFov) * easedProgress,
        }));

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          setHasInitialAnimationPlayed(true);
        }
      };
      requestAnimationFrame(animate);
    }
  }, [bookReady, hasInitialAnimationPlayed]);

  return (
    <div
      className='w-full h-full min-h-[400px] lg:min-h-[600px] bg-transparent transition-opacity duration-1000'
      style={{ opacity: bookReady ? 1 : 0 }}>
      <BookModel
        params={params}
        meshRef={meshRef}
        onReady={setBookReady}
        frontCoverUrl={frontCoverUrl}
        backCoverUrl={backCoverUrl}
      />
    </div>
  );
}
