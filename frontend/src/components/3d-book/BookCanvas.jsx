import { TrackballControls, Environment } from '@react-three/drei';
import { Canvas, useFrame } from '@react-three/fiber';
import React, { Suspense, useRef, useState } from 'react';

import { Book3dModel } from './Book3dModel';
import { CameraController } from './CameraController';

function RenderDetector({ onFirstRender }) {
  const hasRendered = useRef(false);
  useFrame(() => {
    if (!hasRendered.current) {
      hasRendered.current = true;
      onFirstRender();
    }
  });
  return null;
}

export function BookCanvas({
  params,
  materialProps,
  meshRef,
  onReady,
  frontCoverUrl,
  backCoverUrl,
}) {
  const controlsRef = useRef();
  const [hasFirstRender, setHasFirstRender] = useState(false);

  const handleBookReady = (ready) => {
    if (onReady) {
      onReady(ready && hasFirstRender);
    }
  };

  return (
    <div className='w-full h-full'>
      <Canvas
        className='w-full h-full'
        camera={{ position: params.cameraPosition, fov: params.cameraFov }}
        dpr={[1, 2]}>
        <Suspense fallback={null}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[10, 10, 5]} intensity={1} />
          <directionalLight position={[-5, 8, 10]} intensity={0.8} color='#fffacd' />
          <Environment preset='sunset' />
          <RenderDetector onFirstRender={() => setHasFirstRender(true)} />
          <Book3dModel
            params={params}
            materialProps={materialProps}
            meshRef={meshRef}
            onReady={handleBookReady}
            frontCoverUrl={frontCoverUrl}
            backCoverUrl={backCoverUrl}
          />
          <CameraController params={params} />
          <TrackballControls
            ref={controlsRef}
            noPan={true}
            noZoom={true}
            enableRotate={true}
            staticMoving={false}
            dynamicDampingFactor={0.05}
            rotateSpeed={1.5}
            target={params.position}
          />
        </Suspense>
      </Canvas>
    </div>
  );
}
