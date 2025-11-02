import React, { useState, useEffect, useRef, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/loading'
import { AlertCircle, Image as ImageIcon } from 'lucide-react'

/**
 * 图片优化组件属性
 */
export interface OptimizedImageProps {
  src: string
  alt: string
  className?: string
  width?: number
  height?: number
  placeholder?: 'blur' | 'skeleton' | 'color'
  blurDataURL?: string
  lazy?: boolean
  sizes?: string
  quality?: number
  format?: 'webp' | 'avif' | 'auto'
  onLoad?: () => void
  onError?: (error: Error) => void
  fallback?: React.ReactNode
}

/**
 * 优化图片组件
 */
export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  className,
  width,
  height,
  placeholder = 'skeleton',
  blurDataURL,
  lazy = true,
  sizes,
  quality = 75,
  format = 'auto',
  onLoad,
  onError,
  fallback
}) => {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)
  const [imageSrc, setImageSrc] = useState<string>('')
  const imgRef = useRef<HTMLImageElement>(null)

  // 生成优化后的图片URL
  const getOptimizedSrc = useCallback((originalSrc: string) => {
    try {
      const url = new URL(originalSrc, window.location.origin)
      
      // 添加质量参数
      if (quality && quality !== 75) {
        url.searchParams.set('q', quality.toString())
      }
      
      // 添加格式参数
      if (format !== 'auto') {
        url.searchParams.set('f', format)
      }
      
      // 添加尺寸参数
      if (width) {
        url.searchParams.set('w', width.toString())
      }
      if (height) {
        url.searchParams.set('h', height.toString())
      }
      
      return url.toString()
    } catch {
      return originalSrc
    }
  }, [width, height, quality, format])

  useEffect(() => {
    const optimizedSrc = getOptimizedSrc(src)
    setImageSrc(optimizedSrc)
  }, [src, getOptimizedSrc])

  useEffect(() => {
    if (!imageSrc || !imgRef.current) return

    const img = imgRef.current
    
    const handleLoad = () => {
      setIsLoading(false)
      setHasError(false)
      onLoad?.()
    }

    const handleError = () => {
      setIsLoading(false)
      setHasError(true)
      const error = new Error(`Failed to load image: ${src}`)
      onError?.(error)
    }

    img.addEventListener('load', handleLoad)
    img.addEventListener('error', handleError)

    // 如果图片已经加载完成
    if (img.complete) {
      handleLoad()
    }

    return () => {
      img.removeEventListener('load', handleLoad)
      img.removeEventListener('error', handleError)
    }
  }, [imageSrc, src, onLoad, onError])

  // 渲染占位符
  const renderPlaceholder = () => {
    switch (placeholder) {
      case 'blur':
        return (
          <div 
            className={cn(
              "absolute inset-0 bg-cover bg-center filter blur-sm",
              className
            )}
            style={{
              backgroundImage: blurDataURL ? `url(${blurDataURL})` : undefined,
              backgroundColor: blurDataURL ? undefined : '#e5e7eb'
            }}
          />
        )
      case 'color':
        return (
          <div 
            className={cn(
              "absolute inset-0 bg-muted",
              className
            )}
          />
        )
      case 'skeleton':
      default:
        return <Skeleton className="absolute inset-0" />
    }
  }

  // 渲染错误状态
  if (hasError && fallback) {
    return <>{fallback}</>
  }

  if (hasError) {
    return (
      <div className={cn(
        "flex flex-col items-center justify-center bg-muted border-2 border-dashed border-muted-foreground rounded-lg",
        className
      )} style={{ width, height }}>
        <AlertCircle className="w-8 h-8 text-muted-foreground mb-2" />
        <span className="text-sm text-muted-foreground">图片加载失败</span>
      </div>
    )
  }

  return (
    <div className={cn("relative overflow-hidden", className)}>
      {/* 占位符 */}
      {isLoading && renderPlaceholder()}
      
      {/* 实际图片 */}
      <img
        ref={imgRef}
        src={imageSrc}
        alt={alt}
        width={width}
        height={height}
        sizes={sizes}
        loading={lazy ? 'lazy' : 'eager'}
        className={cn(
          "transition-opacity duration-300",
          isLoading ? "opacity-0" : "opacity-100"
        )}
      />
    </div>
  )
}

/**
 * 图片画廊组件
 */
export interface ImageGalleryProps {
  images: Array<{
    src: string
    alt: string
    caption?: string
  }>
  className?: string
  columns?: number
  gap?: number
  lazy?: boolean
  onImageClick?: (index: number) => void
}

export const ImageGallery: React.FC<ImageGalleryProps> = ({
  images,
  className,
  columns = 3,
  gap = 4,
  lazy = true,
  onImageClick
}) => {
  const [loadedImages, setLoadedImages] = useState<Set<number>>(new Set())

  const handleImageLoad = (index: number) => {
    setLoadedImages(prev => new Set(prev).add(index))
  }

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: `repeat(${columns}, 1fr)`,
    gap: `${gap * 0.25}rem`
  }

  return (
    <div className={cn("w-full", className)}>
      <div style={gridStyle}>
        {images.map((image, index) => (
          <div
            key={index}
            className={cn(
              "relative group cursor-pointer overflow-hidden rounded-lg",
              "transform transition-all duration-200 hover:scale-105"
            )}
            onClick={() => onImageClick?.(index)}
          >
            <OptimizedImage
              src={image.src}
              alt={image.alt}
              className="w-full h-48 object-cover"
              lazy={lazy}
              onLoad={() => handleImageLoad(index)}
            />
            
            {/* 加载动画 */}
            {!loadedImages.has(index) && (
              <div className="absolute inset-0 flex items-center justify-center bg-muted/50">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
              </div>
            )}
            
            {/* 悬停信息 */}
            {image.caption && (
              <div className={cn(
                "absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3",
                "transform transition-transform duration-200",
                loadedImages.has(index) ? "translate-y-0" : "translate-y-full"
              )}>
                <p className="text-white text-sm font-medium truncate">
                  {image.caption}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/**
 * 资源预加载Hook
 */
export const useResourcePreload = () => {
  const [preloadedResources, setPreloadedResources] = useState<Set<string>>(new Set())

  const preloadImage = useCallback((src: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (preloadedResources.has(src)) {
        resolve()
        return
      }

      const img = new Image()
      img.onload = () => {
        setPreloadedResources(prev => new Set(prev).add(src))
        resolve()
      }
      img.onerror = reject
      img.src = src
    })
  }, [preloadedResources])

  const preloadImages = useCallback((urls: string[]): Promise<void[]> => {
    return Promise.all(urls.map(preloadImage))
  }, [preloadImage])

  const preloadScript = useCallback((src: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (preloadedResources.has(src)) {
        resolve()
        return
      }

      const script = document.createElement('script')
      script.onload = () => {
        setPreloadedResources(prev => new Set(prev).add(src))
        resolve()
      }
      script.onerror = reject
      script.src = src
      document.head.appendChild(script)
    })
  }, [preloadedResources])

  const preloadStylesheet = useCallback((href: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (preloadedResources.has(href)) {
        resolve()
        return
      }

      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'style'
      link.onload = () => {
        setPreloadedResources(prev => new Set(prev).add(href))
        resolve()
      }
      link.onerror = reject
      link.href = href
      document.head.appendChild(link)
    })
  }, [preloadedResources])

  return {
    preloadImage,
    preloadImages,
    preloadScript,
    preloadStylesheet,
    preloadedResources
  }
}

/**
 * 渐进式图片加载组件
 */
export const ProgressiveImage: React.FC<{
  lowQualitySrc: string
  highQualitySrc: string
  alt: string
  className?: string
  width?: number
  height?: number
}> = ({
  lowQualitySrc,
  highQualitySrc,
  alt,
  className,
  width,
  height
}) => {
  const [currentSrc, setCurrentSrc] = useState(lowQualitySrc)
  const [isHighQualityLoaded, setIsHighQualityLoaded] = useState(false)

  useEffect(() => {
    const img = new Image()
    img.onload = () => {
      setCurrentSrc(highQualitySrc)
      setIsHighQualityLoaded(true)
    }
    img.src = highQualitySrc
  }, [highQualitySrc])

  return (
    <div className={cn("relative overflow-hidden", className)}>
      <img
        src={currentSrc}
        alt={alt}
        width={width}
        height={height}
        className={cn(
          "w-full h-full object-cover transition-all duration-500",
          isHighQualityLoaded ? "filter-none" : "filter blur-sm"
        )}
      />
      
      {!isHighQualityLoaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
        </div>
      )}
    </div>
  )
}

/**
 * 响应式图片组件
 */
export const ResponsiveImage: React.FC<{
  sources: Array<{
    srcSet: string
    media?: string
    type?: string
  }>
  fallbackSrc: string
  alt: string
  className?: string
  sizes?: string
  lazy?: boolean
}> = ({
  sources,
  fallbackSrc,
  alt,
  className,
  sizes,
  lazy = true
}) => {
  const [isLoading, setIsLoading] = useState(true)

  return (
    <div className={cn("relative", className)}>
      <picture>
        {sources.map((source, index) => (
          <source
            key={index}
            srcSet={source.srcSet}
            media={source.media}
            type={source.type}
          />
        ))}
        <img
          src={fallbackSrc}
          alt={alt}
          sizes={sizes}
          loading={lazy ? 'lazy' : 'eager'}
          onLoad={() => setIsLoading(false)}
          className={cn(
            "w-full h-full object-cover transition-opacity duration-300",
            isLoading ? "opacity-0" : "opacity-100"
          )}
        />
      </picture>
      
      {isLoading && (
        <Skeleton className="absolute inset-0" />
      )}
    </div>
  )
}

/**
 * 图片懒加载观察器Hook
 */
export const useLazyLoading = (options?: IntersectionObserverInit) => {
  const [entries, setEntries] = useState<IntersectionObserverEntry[]>([])
  const observer = useRef<IntersectionObserver | null>(null)

  const observe = useCallback((element: Element) => {
    if (observer.current) {
      observer.current.observe(element)
    }
  }, [])

  const unobserve = useCallback((element: Element) => {
    if (observer.current) {
      observer.current.unobserve(element)
    }
  }, [])

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return

    observer.current = new IntersectionObserver((entries) => {
      setEntries(entries)
    }, {
      threshold: 0.1,
      rootMargin: '50px',
      ...options
    })

    return () => {
      if (observer.current) {
        observer.current.disconnect()
      }
    }
  }, [options])

  return {
    entries,
    observe,
    unobserve
  }
}
