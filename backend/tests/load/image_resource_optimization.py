"""
图片懒加载和资源优化实施系统
前端性能优化：图片懒加载、响应式图片、资源压缩、CDN优化
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """资源类型"""
    IMAGE = "image"
    VIDEO = "video"
    FONT = "font"
    CSS = "css"
    JAVASCRIPT = "javascript"
    ICON = "icon"

class OptimizationStrategy(Enum):
    """优化策略"""
    LAZY_LOADING = "lazy_loading"
    RESPONSIVE_IMAGES = "responsive_images"
    IMAGE_COMPRESSION = "image_compression"
    WEBP_CONVERSION = "webp_conversion"
    CDN_OPTIMIZATION = "cdn_optimization"
    PRELOAD_CRITICAL = "preload_critical"

@dataclass
class ResourceAnalysis:
    """资源分析结果"""
    resource_type: ResourceType
    original_size: int
    optimized_size: int
    compression_ratio: float
    loading_strategy: str
    format: str
    dimensions: Optional[Tuple[int, int]]
    optimization_potential: float

@dataclass
class OptimizationImplementation:
    """优化实施"""
    strategy: OptimizationStrategy
    description: str
    code_implementation: str
    estimated_savings: float
    implementation_complexity: str
    browser_support: str

class ImageOptimizer:
    """图片优化器"""
    
    def __init__(self):
        self.image_analysis_results = []
        self.optimization_implementations = []
        
    def analyze_images(self, image_resources: List[Dict[str, Any]]) -> List[ResourceAnalysis]:
        """分析图片资源"""
        print("🖼️ Analyzing image resources...")
        
        for image in image_resources:
            analysis = self._analyze_single_image(image)
            self.image_analysis_results.append(analysis)
        
        return self.image_analysis_results
    
    def _analyze_single_image(self, image: Dict[str, Any]) -> ResourceAnalysis:
        """分析单个图片"""
        resource_type = ResourceType.IMAGE
        original_size = image.get('size', 500000)  # 默认500KB
        original_format = image.get('format', 'jpeg')
        dimensions = image.get('dimensions', (1920, 1080))
        
        # 计算优化潜力
        optimized_size, compression_ratio = self._calculate_optimization_potential(
            original_size, original_format, dimensions
        )
        
        optimization_potential = ((original_size - optimized_size) / original_size) * 100
        
        # 确定加载策略
        loading_strategy = self._determine_loading_strategy(image)
        
        return ResourceAnalysis(
            resource_type=resource_type,
            original_size=original_size,
            optimized_size=optimized_size,
            compression_ratio=compression_ratio,
            loading_strategy=loading_strategy,
            format=original_format,
            dimensions=dimensions,
            optimization_potential=optimization_potential
        )
    
    def _calculate_optimization_potential(self, size: int, format: str, dimensions: Tuple[int, int]) -> Tuple[int, float]:
        """计算优化潜力"""
        # 基于格式和尺寸的优化估算
        if format == 'jpeg':
            optimized_size = int(size * 0.4)  # JPEG可压缩60%
            compression_ratio = 0.4
        elif format == 'png':
            optimized_size = int(size * 0.3)  # PNG可压缩70%
            compression_ratio = 0.3
        elif format == 'webp':
            optimized_size = int(size * 0.5)  # WebP可压缩50%
            compression_ratio = 0.5
        else:
            optimized_size = int(size * 0.6)  # 其他格式默认压缩40%
            compression_ratio = 0.6
        
        # 大尺寸图片有更大优化空间
        pixel_count = dimensions[0] * dimensions[1]
        if pixel_count > 2000000:  # 大于2MP
            optimized_size = int(optimized_size * 0.7)
            compression_ratio *= 0.7
        
        return optimized_size, compression_ratio
    
    def _determine_loading_strategy(self, image: Dict[str, Any]) -> str:
        """确定加载策略"""
        priority = image.get('priority', 'normal')
        location = image.get('location', 'body')
        
        if priority == 'critical' and location == 'above_fold':
            return 'eager'
        elif location == 'below_fold':
            return 'lazy'
        elif image.get('is_gallery', False):
            return 'lazy_with_placeholder'
        else:
            return 'lazy'
    
    def create_lazy_loading_implementation(self) -> OptimizationImplementation:
        """创建懒加载实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.LAZY_LOADING,
            description="实施图片懒加载，提升首屏加载性能",
            code_implementation="""
// 原生懒加载实现
const LazyImage = ({ src, alt, placeholder, className }) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={imgRef} className={className}>
      {isInView ? (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setIsLoaded(true)}
          style={{
            opacity: isLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease'
          }}
        />
      ) : (
        <div className="image-placeholder">
          {placeholder || <div className="skeleton-loader" />}
        </div>
      )}
    </div>
  );
};

// 高级懒加载 - 渐进式加载
const ProgressiveImage = ({ src, placeholderSrc, alt }) => {
  const [imgSrc, setImgSrc] = useState(placeholderSrc || '');
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.src = src;
    img.onload = () => {
      setImgSrc(src);
      setIsLoaded(true);
    };
  }, [src]);

  return (
    <img
      src={imgSrc}
      alt={alt}
      style={{
        filter: isLoaded ? 'none' : 'blur(5px)',
        transition: 'filter 0.3s ease'
      }}
    />
  );
};
            """.strip(),
            estimated_savings=45.0,
            implementation_complexity="medium",
            browser_support="Chrome 77+, Firefox 75+, Safari 15.4+"
        )
    
    def create_responsive_images_implementation(self) -> OptimizationImplementation:
        """创建响应式图片实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.RESPONSIVE_IMAGES,
            description="实施响应式图片，根据设备尺寸加载合适图片",
            code_implementation="""
// 响应式图片组件
const ResponsiveImage = ({ 
  src, 
  alt, 
  sizes, 
  breakpoints = [320, 768, 1024, 1920],
  className 
}) => {
  const generateSrcSet = (baseSrc, breakpoints) => {
    return breakpoints.map(width => 
      \`\${baseSrc}?w=\${width}&q=80 \${width}w\`
    ).join(', ');
  };

  return (
    <picture>
      {/* WebP格式支持 */}
      <source
        type="image/webp"
        srcSet={generateSrcSet(src, breakpoints)}
        sizes={sizes}
      />
      {/* 传统格式fallback */}
      <img
        src={src}
        alt={alt}
        srcSet={generateSrcSet(src, breakpoints)}
        sizes={sizes}
        loading="lazy"
        className={className}
      />
    </picture>
  );
};

// 使用示例
<ResponsiveImage
  src="/images/hero-banner.jpg"
  alt="Hero Banner"
  sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
  breakpoints={[400, 800, 1200, 1600]}
/>

// Art Direction响应式图片
const ArtDirectionImage = () => (
  <picture>
    {/* 移动端 */}
    <source
      media="(max-width: 768px)"
      srcSet="/images/banner-mobile.jpg 1x, /images/banner-mobile@2x.jpg 2x"
    />
    {/* 桌面端 */}
    <source
      media="(min-width: 769px)"
      srcSet="/images/banner-desktop.jpg 1x, /images/banner-desktop@2x.jpg 2x"
    />
    {/* Fallback */}
    <img
      src="/images/banner-desktop.jpg"
      alt="Responsive Banner"
      loading="lazy"
    />
  </picture>
);
            """.strip(),
            estimated_savings=35.0,
            implementation_complexity="medium",
            browser_support="All modern browsers"
        )
    
    def create_image_compression_implementation(self) -> OptimizationImplementation:
        """创建图片压缩实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.IMAGE_COMPRESSION,
            description="优化图片压缩参数，平衡质量和文件大小",
            code_implementation="""
// 图片压缩配置
const imageCompressionConfig = {
  quality: {
    jpeg: 85,
    webp: 80,
    png: 90
  },
  progressive: true,
  optimizationLevel: 3
};

// 构建时图片优化 (webpack配置)
const ImageMinimizerPlugin = require('image-minimizer-webpack-plugin');

module.exports = {
  plugins: [
    new ImageMinimizerPlugin({
      minimizerOptions: {
        plugins: [
          ['imagemin-mozjpeg', { quality: 85, progressive: true }],
          ['imagemin-pngquant', { quality: [0.65, 0.8] }],
          ['imagemin-svgo', { plugins: [{ removeViewBox: false }] }],
        ],
      },
      generator: [
        {
          type: 'asset',
          preset: 'webp-custom-name',
          filename: 'images/[name].[hash:8][ext]',
          minimizerOptions: {
            plugins: [['imagemin-webp', { quality: 80 }]],
          },
        },
      ],
    }),
  ],
};

// 运行时图片优化服务
class ImageOptimizationService {
  static async optimizeImage(imageUrl, options = {}) {
    const {
      width,
      height,
      quality = 80,
      format = 'auto',
      crop = 'smart'
    } = options;

    const params = new URLSearchParams({
      w: width,
      h: height,
      q: quality,
      f: format,
      c: crop
    });

    return \`\${imageUrl}?\${params.toString()}\`;
  }

  static async getResponsiveImageUrl(imageUrl, deviceInfo) {
    const { width, devicePixelRatio = 1 } = deviceInfo;
    const optimizedWidth = Math.floor(width * devicePixelRatio);
    
    return this.optimizeImage(imageUrl, {
      width: optimizedWidth,
      quality: deviceInfo.isMobile ? 75 : 85
    });
  }
}

// 使用示例
const optimizedImageUrl = await ImageOptimizationService.optimizeImage(
  '/images/product.jpg',
  { width: 800, quality: 85, format: 'webp' }
);
            """.strip(),
            estimated_savings=40.0,
            implementation_complexity="high",
            browser_support="All browsers"
        )

class ResourceOptimizer:
    """资源优化器"""
    
    def __init__(self):
        self.image_optimizer = ImageOptimizer()
        self.resource_analysis = []
        self.optimization_plan = {}
        
    def analyze_all_resources(self, resources: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """分析所有资源"""
        print("📊 Analyzing all frontend resources...")
        
        analysis_results = {}
        
        # 分析图片
        if 'images' in resources:
            image_analysis = self.image_optimizer.analyze_images(resources['images'])
            analysis_results['images'] = image_analysis
        
        # 分析其他资源
        for resource_type, resource_list in resources.items():
            if resource_type != 'images':
                analysis_results[resource_type] = self._analyze_generic_resources(
                    resource_list, ResourceType(resource_type)
                )
        
        self.resource_analysis = analysis_results
        return analysis_results
    
    def _analyze_generic_resources(self, resources: List[Dict[str, Any]], 
                                  resource_type: ResourceType) -> List[ResourceAnalysis]:
        """分析通用资源"""
        analysis_results = []
        
        for resource in resources:
            original_size = resource.get('size', 100000)
            
            # 根据资源类型计算优化潜力
            if resource_type == ResourceType.CSS:
                optimized_size = int(original_size * 0.3)  # CSS可压缩70%
                optimization_potential = 70.0
            elif resource_type == ResourceType.JAVASCRIPT:
                optimized_size = int(original_size * 0.4)  # JS可压缩60%
                optimization_potential = 60.0
            elif resource_type == ResourceType.FONT:
                optimized_size = int(original_size * 0.8)  # 字体优化空间较小
                optimization_potential = 20.0
            else:
                optimized_size = int(original_size * 0.5)
                optimization_potential = 50.0
            
            analysis = ResourceAnalysis(
                resource_type=resource_type,
                original_size=original_size,
                optimized_size=optimized_size,
                compression_ratio=optimized_size / original_size,
                loading_strategy=self._determine_resource_loading_strategy(resource),
                format=resource.get('format', 'unknown'),
                dimensions=None,
                optimization_potential=optimization_potential
            )
            
            analysis_results.append(analysis)
        
        return analysis_results
    
    def _determine_resource_loading_strategy(self, resource: Dict[str, Any]) -> str:
        """确定资源加载策略"""
        priority = resource.get('priority', 'normal')
        
        if priority == 'critical':
            return 'preload'
        elif priority == 'high':
            return 'prefetch'
        elif resource.get('is_async', False):
            return 'async_load'
        else:
            return 'defer'
    
    def create_optimization_implementations(self) -> List[OptimizationImplementation]:
        """创建优化实施方案"""
        implementations = []
        
        # 图片懒加载
        implementations.append(self.image_optimizer.create_lazy_loading_implementation())
        
        # 响应式图片
        implementations.append(self.image_optimizer.create_responsive_images_implementation())
        
        # 图片压缩
        implementations.append(self.image_optimizer.create_image_compression_implementation())
        
        # WebP转换
        implementations.append(self._create_webp_conversion_implementation())
        
        # CDN优化
        implementations.append(self._create_cdn_optimization_implementation())
        
        # 关键资源预加载
        implementations.append(self._create_preload_critical_implementation())
        
        # 字体优化
        implementations.append(self._create_font_optimization_implementation())
        
        # CSS优化
        implementations.append(self._create_css_optimization_implementation())
        
        self.optimization_implementations = implementations
        return implementations
    
    def _create_webp_conversion_implementation(self) -> OptimizationImplementation:
        """创建WebP转换实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.WEBP_CONVERSION,
            description="将图片转换为WebP格式，减少文件大小",
            code_implementation="""
// WebP格式检测和fallback
const WebPImage = ({ src, alt, fallbackType = 'jpeg', ...props }) => {
  const [supportsWebP, setSupportsWebP] = useState(false);
  const [imageSrc, setImageSrc] = useState('');

  useEffect(() => {
    const checkWebPSupport = async () => {
      const webP = new Image();
      webP.onload = webP.onerror = () => {
        setSupportsWebP(webP.height === 2);
      };
      webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
    };

    checkWebPSupport();
  }, []);

  useEffect(() => {
    if (supportsWebP) {
      setImageSrc(src.replace(/\\.(jpg|jpeg|png)$/i, '.webp'));
    } else {
      setImageSrc(src);
    }
  }, [supportsWebP, src]);

  return (
    <img
      src={imageSrc}
      alt={alt}
      onError={(e) => {
        if (supportsWebP) {
          e.target.src = src; // fallback to original format
        }
      }}
      {...props}
    />
  );
};

// Picture标签WebP实现
const OptimizedPicture = ({ src, alt, sizes, className }) => (
  <picture>
    <source
      type="image/webp"
      srcSet={\`
        \${src.replace(/\\.(jpg|jpeg|png)$/i, '.webp')} 1x,
        \${src.replace(/\\.(jpg|jpeg|png)$/i, '@2x.webp')} 2x
      \`}
      sizes={sizes}
    />
    <source
      type="image/jpeg"
      srcSet={\`
        \${src} 1x,
        \${src.replace(/\\.(jpg|jpeg)$/i, '@2x.$1')} 2x
      \`}
      sizes={sizes}
    />
    <img
      src={src}
      alt={alt}
      loading="lazy"
      className={className}
    />
  </picture>
);
            """.strip(),
            estimated_savings=25.0,
            implementation_complexity="medium",
            browser_support="Chrome 23+, Firefox 65+, Edge 18+, Safari 14+"
        )
    
    def _create_cdn_optimization_implementation(self) -> OptimizationImplementation:
        """创建CDN优化实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.CDN_OPTIMIZATION,
            description="配置CDN图片优化和缓存策略",
            code_implementation="""
// CDN图片优化配置
const CDNConfig = {
  baseUrl: 'https://cdn.web3search.com',
  imageOptimization: {
    quality: 85,
    autoFormat: true,
    enableWebP: true,
    enableAvif: true,
    sharpen: true,
    removeMetadata: true
  },
  caching: {
    images: '1y',
    assets: '1m',
    html: '1h'
  }
};

// CDN图片URL生成器
class CDNImageBuilder {
  constructor(baseUrl, config) {
    this.baseUrl = baseUrl;
    this.config = config;
  }

  buildUrl(imagePath, options = {}) {
    const {
      width,
      height,
      quality = this.config.imageOptimization.quality,
      format = 'auto',
      crop = 'smart',
      fit = 'cover'
    } = options;

    const params = new URLSearchParams({
      q: quality,
      f: format,
      c: crop,
      fit: fit
    });

    if (width) params.append('w', width);
    if (height) params.append('h', height);

    return \`\${this.baseUrl}/images\${imagePath}?\${params.toString()}\`;
  }

  buildResponsiveSet(imagePath, breakpoints) {
    return breakpoints.map(breakpoint => {
      const url = this.buildUrl(imagePath, { width: breakpoint });
      return \`\${url} \${breakpoint}w\`;
    }).join(', ');
  }
}

// 使用示例
const cdnBuilder = new CDNImageBuilder(CDNConfig.baseUrl, CDNConfig);

const optimizedImageUrl = cdnBuilder.buildUrl('/hero-banner.jpg', {
  width: 1200,
  quality: 85,
  format: 'webp'
});

const responsiveSrcSet = cdnBuilder.buildResponsiveSet(
  '/hero-banner.jpg',
  [400, 800, 1200, 1600]
);

// React组件集成
const CDNImage = ({ src, alt, sizes, className, ...options }) => {
  const [srcSet, setSrcSet] = useState('');
  const [optimizedSrc, setOptimizedSrc] = useState('');

  useEffect(() => {
    setOptimizedSrc(cdnBuilder.buildUrl(src, options));
    if (sizes) {
      setSrcSet(cdnBuilder.buildResponsiveSet(src, [400, 800, 1200, 1600]));
    }
  }, [src, options, sizes]);

  return (
    <img
      src={optimizedSrc}
      srcSet={srcSet}
      sizes={sizes}
      alt={alt}
      loading="lazy"
      className={className}
    />
  );
};
            """.strip(),
            estimated_savings=30.0,
            implementation_complexity="high",
            browser_support="All browsers"
        )
    
    def _create_preload_critical_implementation(self) -> OptimizationImplementation:
        """创建关键资源预加载实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.PRELOAD_CRITICAL,
            description="预加载关键资源，提升首屏渲染速度",
            code_implementation="""
// 关键资源预加载配置
const criticalResources = [
  {
    href: '/fonts/inter-var.woff2',
    as: 'font',
    type: 'font/woff2',
    crossOrigin: 'anonymous'
  },
  {
    href: '/images/hero-banner.webp',
    as: 'image',
    media: '(min-width: 768px)'
  },
  {
    href: '/css/critical.css',
    as: 'style'
  },
  {
    href: '/js/critical.js',
    as: 'script'
  }
];

// 动态预加载关键资源
class ResourcePreloader {
  static preloadResources(resources) {
    resources.forEach(resource => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = resource.href;
      link.as = resource.as;
      
      if (resource.type) link.type = resource.type;
      if (resource.crossOrigin) link.crossOrigin = resource.crossOrigin;
      if (resource.media) link.media = resource.media;
      
      document.head.appendChild(link);
    });
  }

  static preloadImage(src, priority = 'high') {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = src;
    link.setAttribute('importance', priority);
    document.head.appendChild(link);
  }

  static prefetchResource(href) {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = href;
    document.head.appendChild(link);
  }
}

// React Hook for resource preloading
const useResourcePreloading = (resources) => {
  useEffect(() => {
    ResourcePreloader.preloadResources(resources);
  }, [resources]);
};

// 智能预加载策略
class SmartPreloader {
  constructor() {
    this.preloadedResources = new Set();
    this.observerOptions = {
      rootMargin: '50px',
      threshold: 0.1
    };
  }

  preloadOnIntersection(elements, resourceMapper) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const resource = resourceMapper(entry.target);
          if (resource && !this.preloadedResources.has(resource.href)) {
            this.preloadResource(resource);
            this.preloadedResources.add(resource.href);
          }
        }
      });
    }, this.observerOptions);

    elements.forEach(element => observer.observe(element));
  }

  preloadResource(resource) {
    const link = document.createElement('link');
    link.rel = 'preload';
    Object.assign(link, resource);
    document.head.appendChild(link);
  }
}

// 使用示例
const App = () => {
  useResourcePreloading(criticalResources);

  return (
    <div>
      {/* 应用内容 */}
    </div>
  );
};

// 在HTML中直接预加载
/*
<link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin="anonymous">
<link rel="preload" href="/images/hero-banner.webp" as="image" media="(min-width: 768px)">
<link rel="preload" href="/css/critical.css" as="style">
<link rel="preload" href="/js/critical.js" as="script">
*/
            """.strip(),
            estimated_savings=20.0,
            implementation_complexity="medium",
            browser_support="All modern browsers"
        )
    
    def _create_font_optimization_implementation(self) -> OptimizationImplementation:
        """创建字体优化实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.CDN_OPTIMIZATION,
            description="优化字体加载策略，减少字体闪烁",
            code_implementation="""
// 字体优化配置
const fontConfig = {
  display: 'swap',
  preload: true,
  fallbackFonts: {
    heading: ['system-ui', 'sans-serif'],
    body: ['system-ui', 'sans-serif'],
    mono: ['SF Mono', 'Monaco', 'monospace']
  }
};

// 字体预加载
class FontOptimizer {
  static preloadFont(fontUrl, fontFamily) {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'font';
    link.type = 'font/woff2';
    link.crossOrigin = 'anonymous';
    link.href = fontUrl;
    document.head.appendChild(link);

    // 创建字体face
    const fontFace = new FontFace(
      fontFamily,
      `url(${fontUrl})`,
      { display: 'swap' }
    );
    
    document.fonts.add(fontFace);
    fontFace.load();
  }

  static createFontDisplayCSS() {
    return `
      @font-face {
        font-family: 'Inter';
        src: url('/fonts/inter-var.woff2') format('woff2');
        font-display: swap;
        font-weight: 100 900;
        font-style: normal;
      }
    `;
  }

  static optimizeFontLoading() {
    // 禁用FOUC (Flash of Unstyled Content)
    const style = document.createElement('style');
    style.textContent = `
      body {
        font-family: system-ui, -apple-system, sans-serif;
        visibility: visible;
      }
      
      .font-loaded {
        font-family: 'Inter', system-ui, sans-serif;
      }
    `;
    document.head.appendChild(style);

    // 字体加载完成后添加class
    document.fonts.ready.then(() => {
      document.body.classList.add('font-loaded');
    });
  }
}

// React字体组件
const OptimizedFont = ({ 
  children, 
  fontFamily = 'Inter', 
  className = '',
  fallback = 'system-ui' 
}) => {
  const [isFontLoaded, setIsFontLoaded] = useState(false);

  useEffect(() => {
    document.fonts.load('16px Inter').then(() => {
      setIsFontLoaded(true);
    });
  }, []);

  const fontClass = isFontLoaded ? 'font-loaded' : '';
  const combinedClassName = \`\${className} \${fontClass}\`.trim();

  return (
    <div 
      className={combinedClassName}
      style={{
        fontFamily: isFontLoaded ? `'Inter', ${fallback}` : fallback
      }}
    >
      {children}
    </div>
  );
};

// 字体子集化配置
const fontSubsetConfig = {
  subsets: ['latin', 'latin-ext'],
  weights: [400, 500, 600, 700],
  styles: ['normal'],
  display: 'swap'
};
            """.strip(),
            estimated_savings=15.0,
            implementation_complexity="medium",
            browser_support="All modern browsers"
        )
    
    def _create_css_optimization_implementation(self) -> OptimizationImplementation:
        """创建CSS优化实施"""
        return OptimizationImplementation(
            strategy=OptimizationStrategy.CDN_OPTIMIZATION,
            description="优化CSS加载和压缩，减少渲染阻塞",
            code_implementation="""
// CSS优化配置
const cssOptimization = {
  criticalCSS: true,
  unusedCSS: true,
  minification: true,
  inlineCritical: true,
  loadNonCriticalAsync: true
};

// 关键CSS提取
class CriticalCSSOptimizer {
  static extractCriticalCSS() {
    // 使用工具提取首屏CSS
    return `
      /* Critical CSS for above-the-fold content */
      body { margin: 0; font-family: system-ui; }
      .hero { height: 100vh; background: linear-gradient(...); }
      .loading-skeleton { animation: pulse 1.5s ease-in-out; }
    `;
  }

  static inlineCriticalCSS(criticalCSS) {
    const style = document.createElement('style');
    style.textContent = criticalCSS;
    style.setAttribute('data-critical', 'true');
    document.head.insertBefore(style, document.head.firstChild);
  }

  static loadNonCriticalCSS(href) {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'style';
    link.href = href;
    link.onload = function() {
      this.rel = 'stylesheet';
    };
    document.head.appendChild(link);
  }
}

// CSS-in-JS优化
const optimizedStyles = {
  // 使用CSS变量减少重复
  variables: {
    primary: '#3b82f6',
    secondary: '#64748b',
    success: '#10b981'
  },
  
  // 媒体查询优化
  responsive: {
    mobile: '@media (max-width: 768px)',
    tablet: '@media (min-width: 769px) and (max-width: 1024px)',
    desktop: '@media (min-width: 1025px)'
  }
};

// 动态CSS加载
const useDynamicCSS = (href, critical = false) => {
  useEffect(() => {
    if (critical) {
      // 关键CSS立即加载
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      document.head.appendChild(link);
    } else {
      // 非关键CSS异步加载
      CriticalCSSOptimizer.loadNonCriticalCSS(href);
    }
  }, [href, critical]);
};

// CSS压缩和优化 (webpack配置)
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

module.exports = {
  optimization: {
    minimizer: [
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: [
            'default',
            {
              discardComments: { removeAll: true },
              normalizeWhitespace: true,
              minifySelectors: true
            }
          ]
        }
      })
    ]
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: 'css/[name].[contenthash].css',
      chunkFilename: 'css/[name].[contenthash].chunk.css'
    })
  ]
};
            """.strip(),
            estimated_savings=25.0,
            implementation_complexity="medium",
            browser_support="All browsers"
        )
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """生成优化报告"""
        print("📋 Generating comprehensive optimization report...")
        
        total_original_size = 0
        total_optimized_size = 0
        resource_breakdown = {}
        
        # 计算总体优化潜力
        for resource_type, analyses in self.resource_analysis.items():
            type_original = sum(analysis.original_size for analysis in analyses)
            type_optimized = sum(analysis.optimized_size for analysis in analyses)
            type_savings = type_original - type_optimized
            
            resource_breakdown[resource_type] = {
                "original_size": type_original,
                "optimized_size": type_optimized,
                "savings": type_savings,
                "savings_percent": (type_savings / type_original * 100) if type_original > 0 else 0,
                "count": len(analyses)
            }
            
            total_original_size += type_original
            total_optimized_size += type_optimized
        
        total_savings = total_original_size - total_optimized_size
        total_savings_percent = (total_savings / total_original_size * 100) if total_original_size > 0 else 0
        
        # 创建实施计划
        implementation_plan = self._create_implementation_plan()
        
        optimization_report = {
            "summary": {
                "total_original_size": total_original_size,
                "total_optimized_size": total_optimized_size,
                "total_savings": total_savings,
                "savings_percent": total_savings_percent,
                "resources_analyzed": sum(len(analyses) for analyses in self.resource_analysis.values())
            },
            "resource_breakdown": resource_breakdown,
            "optimization_implementations": [asdict(impl) for impl in self.optimization_implementations],
            "implementation_plan": implementation_plan,
            "performance_targets": {
                "image_size_reduction": "> 50%",
                "first_contentful_paint": "< 1.5s",
                "largest_contentful_paint": "< 2.5s",
                "cumulative_layout_shift": "< 0.1"
            },
            "monitoring_strategy": {
                "tools": ["Lighthouse", "WebPageTest", "Chrome DevTools"],
                "metrics": ["FCP", "LCP", "CLS", "FID"],
                "frequency": "weekly"
            }
        }
        
        return optimization_report
    
    def _create_implementation_plan(self) -> Dict[str, Any]:
        """创建实施计划"""
        return {
            "phase_1_immediate": {
                "duration": "1-2 days",
                "tasks": [
                    "Implement native lazy loading for images",
                    "Add WebP format support with fallbacks",
                    "Configure CDN image optimization",
                    "Preload critical fonts and images"
                ],
                "expected_impact": "30-40% size reduction",
                "complexity": "Low-Medium"
            },
            "phase_2_optimization": {
                "duration": "3-4 days",
                "tasks": [
                    "Implement responsive images with srcset",
                    "Add progressive image loading",
                    "Optimize CSS delivery and critical CSS",
                    "Configure font loading strategies"
                ],
                "expected_impact": "20-30% performance improvement",
                "complexity": "Medium"
            },
            "phase_3_advanced": {
                "duration": "5-7 days",
                "tasks": [
                    "Implement adaptive image loading",
                    "Add intelligent preloading strategies",
                    "Configure advanced caching policies",
                    "Set up image compression pipeline"
                ],
                "expected_impact": "15-25% additional optimization",
                "complexity": "High"
            }
        }

def main():
    """主函数 - 图片懒加载和资源优化"""
    print("🚀 Starting Image Lazy Loading and Resource Optimization...")
    
    # 创建资源优化器
    optimizer = ResourceOptimizer()
    
    # 模拟资源数据
    resources = {
        "images": [
            {
                "name": "hero-banner",
                "size": 800000,  # 800KB
                "format": "jpeg",
                "dimensions": (1920, 1080),
                "priority": "critical",
                "location": "above_fold"
            },
            {
                "name": "product-gallery-1",
                "size": 400000,  # 400KB
                "format": "jpeg",
                "dimensions": (800, 600),
                "priority": "normal",
                "location": "below_fold",
                "is_gallery": True
            },
            {
                "name": "team-photo",
                "size": 250000,  # 250KB
                "format": "png",
                "dimensions": (400, 400),
                "priority": "low",
                "location": "below_fold"
            },
            {
                "name": "background-pattern",
                "size": 150000,  # 150KB
                "format": "webp",
                "dimensions": (1200, 800),
                "priority": "normal",
                "location": "background"
            }
        ],
        "css": [
            {
                "name": "main-styles",
                "size": 150000,  # 150KB
                "format": "css",
                "priority": "critical"
            },
            {
                "name": "component-styles",
                "size": 80000,   # 80KB
                "format": "css",
                "priority": "normal"
            }
        ],
        "javascript": [
            {
                "name": "app-bundle",
                "size": 500000,  # 500KB
                "format": "js",
                "priority": "critical"
            },
            {
                "name": "vendor-bundle",
                "size": 300000,  # 300KB
                "format": "js",
                "priority": "normal"
            }
        ],
        "font": [
            {
                "name": "inter-regular",
                "size": 80000,   # 80KB
                "format": "woff2",
                "priority": "critical"
            },
            {
                "name": "inter-bold",
                "size": 85000,   # 85KB
                "format": "woff2",
                "priority": "normal"
            }
        ]
    }
    
    # 分析所有资源
    analysis_results = optimizer.analyze_all_resources(resources)
    
    # 创建优化实施方案
    implementations = optimizer.create_optimization_implementations()
    
    # 显示分析结果
    print(f"\n📊 Resource Analysis Results:")
    
    for resource_type, analyses in analysis_results.items():
        total_original = sum(analysis.original_size for analysis in analyses)
        total_optimized = sum(analysis.optimized_size for analysis in analyses)
        savings = total_original - total_optimized
        savings_percent = (savings / total_original * 100) if total_original > 0 else 0
        
        print(f"\n• {resource_type.title()}:")
        print(f"  Resources: {len(analyses)}")
        print(f"  Original Size: {total_original / 1024:.1f}KB")
        print(f"  Optimized Size: {total_optimized / 1024:.1f}KB")
        print(f"  Savings: {savings / 1024:.1f}KB ({savings_percent:.1f}%)")
    
    # 显示优化实施方案
    print(f"\n💡 Optimization Implementations ({len(implementations)}):")
    
    for i, impl in enumerate(implementations, 1):
        impl_strategy = impl.strategy.value if hasattr(impl.strategy, 'value') else str(impl.strategy)
        print(f"\n{i}. {impl_strategy.replace('_', ' ').title()}")
        print(f"   Estimated Savings: {impl.estimated_savings:.1f}%")
        print(f"   Complexity: {impl.implementation_complexity}")
        print(f"   Browser Support: {impl.browser_support}")
        print(f"   Description: {impl.description}")
    
    # 生成优化报告
    optimization_report = optimizer.generate_optimization_report()
    
    # 显示摘要
    summary = optimization_report["summary"]
    print(f"\n📈 Optimization Summary:")
    print(f"  Total Resources Analyzed: {summary['resources_analyzed']}")
    print(f"  Total Original Size: {summary['total_original_size'] / 1024:.1f}KB")
    print(f"  Total Optimized Size: {summary['total_optimized_size'] / 1024:.1f}KB")
    print(f"  Total Savings: {summary['total_savings'] / 1024:.1f}KB ({summary['savings_percent']:.1f}%)")
    
    # 显示实施计划
    implementation_plan = optimization_report["implementation_plan"]
    print(f"\n🚀 Implementation Plan:")
    
    for phase_name, phase_data in implementation_plan.items():
        print(f"\n• {phase_name.replace('_', ' ').title()}:")
        print(f"  Duration: {phase_data['duration']}")
        print(f"  Expected Impact: {phase_data['expected_impact']}")
        print(f"  Complexity: {phase_data['complexity']}")
        print(f"  Tasks:")
        for task in phase_data['tasks']:
            print(f"    - {task}")
    
    # 保存优化报告
    with open("image_resource_optimization_report.json", "w") as f:
        json.dump(optimization_report, f, indent=2, default=str)
    
    print(f"\n✅ Image Lazy Loading and Resource Optimization completed!")
    print("📁 Optimization report saved to: image_resource_optimization_report.json")
    
    return optimization_report

if __name__ == "__main__":
    main()
