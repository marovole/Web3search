import React, { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface LazyImageProps {
  src: string
  alt: string
  className?: string
  width?: number | string
  height?: number | string
  placeholderSrc?: string
  webpSrc?: string
  avifSrc?: string
  sizes?: string
  onLoad?: () => void
  onError?: () => void
  style?: React.CSSProperties
}

/**
 * 懒加载图片组件
 * 支持多种图片格式、占位符和加载状态
 */
export function LazyImage({
  src,
  alt,
  className,
  width,
  height,
  placeholderSrc,
  webpSrc,
  avifSrc,
  sizes,
  onLoad,
  onError,
  style,
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(false)
  const [hasError, setHasError] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.disconnect()
        }
      },
      {
        rootMargin: '50px 0px', // 提前50px开始加载
        threshold: 0.1,
      }
    )

    if (containerRef.current) {
      observer.observe(containerRef.current)
    }

    return () => observer.disconnect()
  }, [])

  const handleLoad = () => {
    setIsLoaded(true)
    onLoad?.()
  }

  const handleError = () => {
    setHasError(true)
    onError?.()
  }

  // 生成srcset
  const generateSrcSet = (baseSrc: string) => {
    // 简单的示例：支持不同尺寸
    const sizes = [1, 2] // 1x, 2x
    return sizes
      .map(size => {
        // 假设图片URL支持尺寸参数
        const sizedSrc = baseSrc.includes('?')
          ? `${baseSrc}&w=${size * 800}`
          : `${baseSrc}?w=${size * 800}`
        return `${sizedSrc} ${size}x`
      })
      .join(', ')
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative overflow-hidden',
        className
      )}
      style={{ width, height, ...style }}
    >
      {/* 占位符 */}
      {(!isLoaded || hasError) && placeholderSrc && (
        <img
          src={placeholderSrc}
          alt=""
          className="absolute inset-0 w-full h-full object-cover blur-sm scale-110"
          aria-hidden="true"
        />
      )}

      {/* 骨架屏 */}
      {!isLoaded && !hasError && !placeholderSrc && (
        <div className="absolute inset-0 bg-muted animate-pulse" />
      )}

      {/* 主图片 */}
      {isInView && !hasError && (
        <picture>
          {/* AVIF格式 - 最高效 */}
          {avifSrc && (
            <source
              srcSet={generateSrcSet(avifSrc)}
              type="image/avif"
              sizes={sizes}
            />
          )}
          {/* WebP格式 - 次选 */}
          {webpSrc && (
            <source
              srcSet={generateSrcSet(webpSrc)}
              type="image/webp"
              sizes={sizes}
            />
          )}
          {/* 原始格式 - fallback */}
          <img
            ref={imgRef}
            src={src}
            srcSet={generateSrcSet(src)}
            sizes={sizes}
            alt={alt}
            className={cn(
              'w-full h-full object-cover transition-opacity duration-300',
              isLoaded ? 'opacity-100' : 'opacity-0'
            )}
            onLoad={handleLoad}
            onError={handleError}
            loading="lazy"
            decoding="async"
          />
        </picture>
      )}

      {/* 错误状态 */}
      {hasError && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted text-muted-foreground">
          <div className="text-center p-4">
            <svg
              className="w-8 h-8 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-sm">图片加载失败</p>
          </div>
        </div>
      )}

      {/* 加载指示器 */}
      {!isLoaded && isInView && !hasError && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  )
}

/**
 * 渐进式图片加载组件
 * 支持从低质量到高质量的平滑过渡
 */
export function ProgressiveImage({
  lowQualitySrc,
  highQualitySrc,
  alt,
  className,
  width,
  height,
  onLoad,
  onError,
  placeholderSrc,
  webpSrc,
  avifSrc,
  sizes,
  style,
}: LazyImageProps & { lowQualitySrc: string; highQualitySrc: string }) {
  const [currentSrc, setCurrentSrc] = useState(lowQualitySrc)
  const [isHighQualityLoaded, setIsHighQualityLoaded] = useState(false)

  useEffect(() => {
    const img = new Image()
    img.src = highQualitySrc
    img.onload = () => {
      setCurrentSrc(highQualitySrc)
      setIsHighQualityLoaded(true)
    }
  }, [highQualitySrc])

  return (
    <LazyImage
      src={currentSrc}
      alt={alt}
      className={cn(
        'transition-all duration-500',
        isHighQualityLoaded ? 'blur-0' : 'blur-sm',
        className
      )}
      width={width}
      height={height}
      onLoad={onLoad}
      onError={onError}
      placeholderSrc={placeholderSrc}
      webpSrc={webpSrc}
      avifSrc={avifSrc}
      sizes={sizes}
      style={style}
    />
  )
}

/**
 * Avatar图片组件
 * 专门用于用户头像的懒加载组件
 */
export function LazyAvatar({
  src,
  alt,
  size = 40,
  className,
  ...props
}: Omit<LazyImageProps, 'width' | 'height'> & { size?: number }) {
  return (
    <LazyImage
      src={src}
      alt={alt}
      width={size}
      height={size}
      className={cn(
        'rounded-full object-cover flex-shrink-0',
        className
      )}
      placeholderSrc={`data:image/svg+xml,${encodeURIComponent(
        `<svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
          <rect width="${size}" height="${size}" fill="#e5e7eb"/>
          <circle cx="${size/2}" cy="${size/2}" r="${size/3}" fill="#9ca3af"/>
        </svg>`
      )}`}
      {...props}
    />
  )
}