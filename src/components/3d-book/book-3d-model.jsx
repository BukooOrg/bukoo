import { useGLTF } from "@react-three/drei"
import { useRef, useEffect, useState } from "react"
import * as THREE from "three"
import { generateUVForBothCovers } from "./uv-debugger"
import { TexturePreloader } from "./texture-preloader"

export function Book({
  params,
  materialProps,
  meshRef,
  onReady,
  frontCoverUrl,
  backCoverUrl,
}) {
  const { scene } = useGLTF("/models/book_red.glb")
  const bookRef = useRef()
  const [bookScene, setBookScene] = useState(null)
  const [object2Mesh, setObject2Mesh] = useState(null)
  const [uvGenerated, setUvGenerated] = useState(false)
  const [frontTexture, setFrontTexture] = useState(null)
  const [backTexture, setBackTexture] = useState(null)
  const [combinedTexture, setCombinedTexture] = useState(null)

  // We only strictly need the scene to show *something*
  const isReady = !!bookScene

  useEffect(() => {
    if (onReady) {
      onReady(isReady)
    }
  }, [isReady, onReady])

  useEffect(() => {
    if (scene && !bookScene) {
      const clonedScene = scene.clone()
      setBookScene(clonedScene)
    }
  }, [scene, bookScene])

  useEffect(() => {
    if (!frontCoverUrl) return

    const preloader = TexturePreloader.getInstance()

    const loadTexture = async (url, isFront) => {
      try {
        const img = await preloader.preloadImage(url)
        const texture = new THREE.Texture(img)
        texture.flipY = true
        texture.colorSpace = THREE.SRGBColorSpace
        texture.needsUpdate = true
        if (isFront) {
          setFrontTexture(texture)
        } else {
          setBackTexture(texture)
        }
      } catch (error) {
        console.error(`Failed to load texture: ${url}`, error)
      }
    }

    loadTexture(frontCoverUrl, true)
    if (backCoverUrl) {
      loadTexture(backCoverUrl, false)
    } else {
      setBackTexture(null)
    }
  }, [frontCoverUrl, backCoverUrl])

  useEffect(() => {
    if (bookScene && !uvGenerated) {
      const sketchfabModel = bookScene.getObjectByName("Sketchfab_model")
      if (sketchfabModel) {
        const geode = sketchfabModel.getObjectByName("Geode")
        if (geode) {
          const object2 = geode.getObjectByName("Object_2")
          if (object2 && object2.material) {
            const mesh = object2
            generateUVForBothCovers(mesh)
            setUvGenerated(true)
            setObject2Mesh(mesh)
            meshRef.current = mesh
          }
        }
      }
    }
  }, [bookScene, meshRef, uvGenerated])

  const createCombinedTexture = (fText, bText) => {
    try {
      const canvas = document.createElement("canvas")
      const ctx = canvas.getContext("2d")
      if (!ctx) return null

      const fImg = fText.image
      canvas.width = fImg.width * 2
      canvas.height = fImg.height

      // Draw front cover
      ctx.drawImage(fImg, 0, 0, fImg.width, fImg.height)

      if (bText && bText.image) {
        // Draw actual back cover
        ctx.drawImage(bText.image, fImg.width, 0, fImg.width, fImg.height)
      } else {
        // "Scan edges" logic
        const edgeCanvas = document.createElement("canvas")
        edgeCanvas.width = 1
        edgeCanvas.height = fImg.height
        const edgeCtx = edgeCanvas.getContext("2d")
        edgeCtx.drawImage(fImg, fImg.width - 1, 0, 1, fImg.height, 0, 0, 1, fImg.height)
        
        ctx.fillStyle = "rgba(0,0,0,1)"
        try {
          const pixel = edgeCtx.getImageData(0, Math.floor(fImg.height / 2), 1, 1).data
          ctx.fillStyle = `rgb(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`
        } catch (e) {
          // Silent fallback
        }
        
        ctx.fillRect(fImg.width, 0, fImg.width, fImg.height)
      }

      const combined = new THREE.CanvasTexture(canvas)
      combined.flipY = true
      combined.colorSpace = THREE.SRGBColorSpace
      combined.needsUpdate = true
      return combined
    } catch (err) {
      console.error("Error creating combined texture:", err)
      return null
    }
  }

  useEffect(() => {
    if (frontTexture) {
      const combined = createCombinedTexture(frontTexture, backTexture)
      if (combined) {
        setCombinedTexture(combined)
      }
    }
  }, [frontTexture, backTexture])

  useEffect(() => {
    if (object2Mesh && uvGenerated) {
      const mesh = object2Mesh
      let material = mesh.userData.originalMaterial || mesh.material
      if (Array.isArray(material)) material = material[0]

      const clonedMaterial = material.clone()
      if (combinedTexture) {
        clonedMaterial.map = combinedTexture
        clonedMaterial.color.setRGB(1, 1, 1)
      } else {
        clonedMaterial.color.set("#8B0000") // Fallback dark red
      }
      clonedMaterial.metalness = 0.4
      clonedMaterial.roughness = 1
      clonedMaterial.polygonOffset = true
      clonedMaterial.polygonOffsetFactor = -1
      clonedMaterial.polygonOffsetUnits = -1
      clonedMaterial.needsUpdate = true

      mesh.material = clonedMaterial
    }
  }, [object2Mesh, combinedTexture, uvGenerated])

  if (!bookScene) return null

  return (
    <primitive
      ref={bookRef}
      object={bookScene}
      scale={params.scale}
      position={params.position}
      rotation={params.rotation}
    />
  )
}
