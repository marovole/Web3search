import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { 
  BookOpen, 
  Search, 
  HelpCircle, 
  FileText, 
  Video, 
  Download,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Clock,
  Eye,
  Star,
  Filter,
  ChevronDown,
  ChevronRight,
  Tag,
  Folder,
  Home
} from 'lucide-react'

/**
 * 文档类型
 */
export type DocumentType = 'article' | 'guide' | 'tutorial' | 'video' | 'faq' | 'api'

/**
 * 文档分类
 */
export interface DocumentCategory {
  id: string
  name: string
  description: string
  icon?: React.ReactNode
  parentId?: string
  order: number
}

/**
 * 帮助文档项
 */
export interface HelpDocument {
  id: string
  title: string
  description: string
  content: string
  type: DocumentType
  category: string
  tags: string[]
  author?: string
  lastUpdated: number
  readTime: number // 预计阅读时间（分钟）
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  language: string
  version?: string
  attachments?: Array<{
    name: string
    url: string
    type: string
    size: number
  }>
  relatedDocuments?: string[]
  metadata?: {
    views: number
    likes: number
    rating: number
    featured: boolean
  }
}

/**
 * FAQ项
 */
export interface FAQItem {
  id: string
  question: string
  answer: string
  category: string
  tags: string[]
  helpful: number
  notHelpful: number
  lastUpdated: number
  related?: string[]
}

/**
 * 帮助文档系统Hook
 */
export const useHelpSystem = (documents: HelpDocument[], faqs: FAQItem[]) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedType, setSelectedType] = useState<DocumentType | 'all'>('all')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [viewHistory, setViewHistory] = useState<string[]>([])

  // 从存储中恢复历史记录
  useEffect(() => {
    try {
      const saved = localStorage.getItem('help_view_history')
      if (saved) {
        setViewHistory(JSON.parse(saved))
      }
    } catch (error) {
      console.warn('Failed to restore help view history:', error)
    }
  }, [])

  const saveViewHistory = useCallback((history: string[]) => {
    try {
      localStorage.setItem('help_view_history', JSON.stringify(history))
    } catch (error) {
      console.warn('Failed to save help view history:', error)
    }
  }, [])

  const addToHistory = useCallback((documentId: string) => {
    setViewHistory(prev => {
      const newHistory = [documentId, ...prev.filter(id => id !== documentId)].slice(0, 20)
      saveViewHistory(newHistory)
      return newHistory
    })
  }, [saveViewHistory])

  const filteredDocuments = useMemo(() => {
    return documents.filter(doc => {
      // 搜索过滤
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase()
        const matchesSearch = 
          doc.title.toLowerCase().includes(searchLower) ||
          doc.description.toLowerCase().includes(searchLower) ||
          doc.content.toLowerCase().includes(searchLower) ||
          doc.tags.some(tag => tag.toLowerCase().includes(searchLower))
        
        if (!matchesSearch) return false
      }

      // 分类过滤
      if (selectedCategory !== 'all' && doc.category !== selectedCategory) {
        return false
      }

      // 类型过滤
      if (selectedType !== 'all' && doc.type !== selectedType) {
        return false
      }

      // 标签过滤
      if (selectedTags.length > 0) {
        const hasSelectedTag = selectedTags.some(tag => doc.tags.includes(tag))
        if (!hasSelectedTag) return false
      }

      return true
    })
  }, [documents, searchTerm, selectedCategory, selectedType, selectedTags])

  const filteredFAQs = useMemo(() => {
    return faqs.filter(faq => {
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase()
        const matchesSearch = 
          faq.question.toLowerCase().includes(searchLower) ||
          faq.answer.toLowerCase().includes(searchLower) ||
          faq.tags.some(tag => tag.toLowerCase().includes(searchLower))
        
        if (!matchesSearch) return false
      }

      if (selectedCategory !== 'all' && faq.category !== selectedCategory) {
        return false
      }

      if (selectedTags.length > 0) {
        const hasSelectedTag = selectedTags.some(tag => faq.tags.includes(tag))
        if (!hasSelectedTag) return false
      }

      return true
    })
  }, [faqs, searchTerm, selectedCategory, selectedTags])

  const getPopularDocuments = useCallback((limit: number = 5) => {
    return documents
      .sort((a, b) => (b.metadata?.views || 0) - (a.metadata?.views || 0))
      .slice(0, limit)
  }, [documents])

  const getRecentDocuments = useCallback((limit: number = 5) => {
    return documents
      .sort((a, b) => b.lastUpdated - a.lastUpdated)
      .slice(0, limit)
  }, [documents])

  const getFeaturedDocuments = useCallback((limit: number = 3) => {
    return documents
      .filter(doc => doc.metadata?.featured)
      .slice(0, limit)
  }, [documents])

  const getRelatedDocuments = useCallback((documentId: string, limit: number = 3) => {
    const doc = documents.find(d => d.id === documentId)
    if (!doc) return []

    return documents
      .filter(d => 
        d.id !== documentId &&
        (d.category === doc.category || 
         d.tags.some(tag => doc.tags.includes(tag)) ||
         doc.relatedDocuments?.includes(d.id))
      )
      .sort((a, b) => (b.metadata?.views || 0) - (a.metadata?.views || 0))
      .slice(0, limit)
  }, [documents])

  return {
    searchTerm,
    setSearchTerm,
    selectedCategory,
    setSelectedCategory,
    selectedType,
    setSelectedType,
    selectedTags,
    setSelectedTags,
    viewHistory,
    addToHistory,
    filteredDocuments,
    filteredFAQs,
    getPopularDocuments,
    getRecentDocuments,
    getFeaturedDocuments,
    getRelatedDocuments
  }
}

/**
 * 文档卡片组件
 */
export const DocumentCard: React.FC<{
  document: HelpDocument
  onClick: (document: HelpDocument) => void
  onLike?: (documentId: string) => void
  showMetadata?: boolean
  className?: string
}> = ({ document, onClick, onLike, showMetadata = true, className }) => {
  const getTypeIcon = (type: DocumentType) => {
    switch (type) {
      case 'article':
        return <FileText className="w-4 h-4" />
      case 'guide':
        return <BookOpen className="w-4 h-4" />
      case 'tutorial':
        return <Video className="w-4 h-4" />
      case 'video':
        return <Video className="w-4 h-4" />
      case 'faq':
        return <HelpCircle className="w-4 h-4" />
      case 'api':
        return <Code className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  const getTypeColor = (type: DocumentType) => {
    switch (type) {
      case 'article':
        return 'bg-blue-100 text-blue-700 border-blue-200'
      case 'guide':
        return 'bg-green-100 text-green-700 border-green-200'
      case 'tutorial':
        return 'bg-purple-100 text-purple-700 border-purple-200'
      case 'video':
        return 'bg-red-100 text-red-700 border-red-200'
      case 'faq':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200'
      case 'api':
        return 'bg-gray-100 text-gray-700 border-gray-200'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner':
        return 'bg-green-50 text-green-600'
      case 'intermediate':
        return 'bg-yellow-50 text-yellow-600'
      case 'advanced':
        return 'bg-red-50 text-red-600'
      default:
        return 'bg-gray-50 text-gray-600'
    }
  }

  return (
    <Card 
      className={cn(
        "p-4 space-y-3 hover:shadow-md transition-shadow cursor-pointer",
        document.metadata?.featured && "border-primary bg-primary/5",
        className
      )}
      onClick={() => onClick(document)}
    >
      {/* 头部 */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className={cn("p-1 rounded", getTypeColor(document.type))}>
            {getTypeIcon(document.type)}
          </div>
          <div>
            <h3 className="font-semibold text-foreground line-clamp-1">
              {document.title}
            </h3>
            {document.metadata?.featured && (
              <div className="flex items-center gap-1 text-xs text-primary">
                <Star className="w-3 h-3 fill-current" />
                精选
              </div>
            )}
          </div>
        </div>
        
        {onLike && (
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation()
              onLike(document.id)
            }}
            className="h-8 w-8 p-0"
          >
            <ThumbsUp className={cn(
              "w-4 h-4",
              document.metadata?.likes ? "text-blue-500" : "text-gray-400"
            )} />
          </Button>
        )}
      </div>

      {/* 描述 */}
      <p className="text-sm text-muted-foreground line-clamp-2">
        {document.description}
      </p>

      {/* 元数据 */}
      {showMetadata && (
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className={cn(
            "px-2 py-1 rounded",
            getDifficultyColor(document.difficulty)
          )}>
            {document.difficulty === 'beginner' && '入门'}
            {document.difficulty === 'intermediate' && '进阶'}
            {document.difficulty === 'advanced' && '高级'}
          </span>
          
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {document.readTime} 分钟
          </span>
          
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            {document.metadata?.views || 0}
          </span>
          
          {document.author && (
            <span>作者: {document.author}</span>
          )}
        </div>
      )}

      {/* 标签 */}
      {document.tags.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {document.tags.slice(0, 3).map(tag => (
            <span
              key={tag}
              className="text-xs px-2 py-1 bg-muted text-muted-foreground rounded"
            >
              {tag}
            </span>
          ))}
          {document.tags.length > 3 && (
            <span className="text-xs px-2 py-1 bg-muted text-muted-foreground rounded">
              +{document.tags.length - 3}
            </span>
          )}
        </div>
      )}
    </Card>
  )
}

/**
 * FAQ项组件
 */
export const FAQItem: React.FC<{
  faq: FAQItem
  onHelpful?: (faqId: string, helpful: boolean) => void
  className?: string
}> = ({ faq, onHelpful, className }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [hasVoted, setHasVoted] = useState(false)

  const handleHelpful = (helpful: boolean) => {
    if (!hasVoted && onHelpful) {
      onHelpful(faq.id, helpful)
      setHasVoted(true)
    }
  }

  return (
    <Card className={cn("p-4 space-y-3", className)}>
      {/* 问题 */}
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="font-medium text-foreground flex-1">
          {faq.question}
        </h3>
        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </Button>
      </div>

      {/* 答案 */}
      {isExpanded && (
        <div className="space-y-3">
          <div className="text-sm text-muted-foreground pt-2 border-t">
            {faq.answer}
          </div>

          {/* 反馈 */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">这个答案有帮助吗？</span>
              <div className="flex gap-1">
                <Button
                  variant={hasVoted ? "outline" : "ghost"}
                  size="sm"
                  onClick={() => handleHelpful(true)}
                  className={cn(
                    "h-6 px-2 text-xs",
                    hasVoted && "text-green-600 border-green-200"
                  )}
                >
                  <ThumbsUp className="w-3 h-3 mr-1" />
                  {faq.helpful}
                </Button>
                <Button
                  variant={hasVoted ? "outline" : "ghost"}
                  size="sm"
                  onClick={() => handleHelpful(false)}
                  className={cn(
                    "h-6 px-2 text-xs",
                    hasVoted && "text-red-600 border-red-200"
                  )}
                >
                  <ThumbsDown className="w-3 h-3 mr-1" />
                  {faq.notHelpful}
                </Button>
              </div>
            </div>

            <div className="text-xs text-muted-foreground">
              更新于 {new Date(faq.lastUpdated).toLocaleDateString()}
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}

/**
 * 帮助文档中心组件
 */
export const HelpCenter: React.FC<{
  documents: HelpDocument[]
  faqs: FAQItem[]
  categories: DocumentCategory[]
  className?: string
}> = ({ documents, faqs, categories, className }) => {
  const [activeTab, setActiveTab] = useState<'documents' | 'faqs'>('documents')
  const [selectedDocument, setSelectedDocument] = useState<HelpDocument | null>(null)
  
  const helpSystem = useHelpSystem(documents, faqs)

  const handleDocumentClick = (document: HelpDocument) => {
    setSelectedDocument(document)
    helpSystem.addToHistory(document.id)
  }

  const handleFAQHelpful = (faqId: string, helpful: boolean) => {
    // 这里可以调用API更新FAQ的反馈数据
    console.log(`FAQ ${faqId} was ${helpful ? 'helpful' : 'not helpful'}`)
  }

  const handleDocumentLike = (documentId: string) => {
    // 这里可以调用API更新文档的点赞数据
    console.log(`Document ${documentId} liked`)
  }

  if (selectedDocument) {
    return (
      <DocumentViewer
        document={selectedDocument}
        onBack={() => setSelectedDocument(null)}
        relatedDocuments={helpSystem.getRelatedDocuments(selectedDocument.id)}
        onRelatedClick={handleDocumentClick}
      />
    )
  }

  return (
    <div className={cn("w-full max-w-6xl mx-auto space-y-6", className)}>
      {/* 头部搜索 */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <BookOpen className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold">帮助中心</h1>
        </div>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="搜索帮助文档和常见问题..."
            value={helpSystem.searchTerm}
            onChange={(e) => helpSystem.setSearchTerm(e.target.value)}
            className="pl-10 pr-4"
          />
        </div>
      </Card>

      {/* 快速访问 */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Star className="w-5 h-5 text-yellow-500" />
            <h3 className="font-semibold">精选文档</h3>
          </div>
          <div className="space-y-2">
            {helpSystem.getFeaturedDocuments(3).map(doc => (
              <div
                key={doc.id}
                className="text-sm cursor-pointer hover:text-primary"
                onClick={() => handleDocumentClick(doc)}
              >
                {doc.title}
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-5 h-5 text-green-500" />
            <h3 className="font-semibold">热门文档</h3>
          </div>
          <div className="space-y-2">
            {helpSystem.getPopularDocuments(3).map(doc => (
              <div
                key={doc.id}
                className="text-sm cursor-pointer hover:text-primary"
                onClick={() => handleDocumentClick(doc)}
              >
                {doc.title}
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-5 h-5 text-blue-500" />
            <h3 className="font-semibold">最近更新</h3>
          </div>
          <div className="space-y-2">
            {helpSystem.getRecentDocuments(3).map(doc => (
              <div
                key={doc.id}
                className="text-sm cursor-pointer hover:text-primary"
                onClick={() => handleDocumentClick(doc)}
              >
                {doc.title}
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 标签页 */}
      <div className="flex gap-2 border-b">
        <Button
          variant={activeTab === 'documents' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('documents')}
        >
          帮助文档 ({helpSystem.filteredDocuments.length})
        </Button>
        <Button
          variant={activeTab === 'faqs' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('faqs')}
        >
          常见问题 ({helpSystem.filteredFAQs.length})
        </Button>
      </div>

      {/* 筛选器 */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* 分类筛选 */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <select
            value={helpSystem.selectedCategory}
            onChange={(e) => helpSystem.setSelectedCategory(e.target.value)}
            className="border rounded px-3 py-1 text-sm"
          >
            <option value="all">全部分类</option>
            {categories.map(category => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>

        {/* 类型筛选 */}
        {activeTab === 'documents' && (
          <div className="flex items-center gap-2">
            <select
              value={helpSystem.selectedType}
              onChange={(e) => helpSystem.setSelectedType(e.target.value as any)}
              className="border rounded px-3 py-1 text-sm"
            >
              <option value="all">全部类型</option>
              <option value="article">文章</option>
              <option value="guide">指南</option>
              <option value="tutorial">教程</option>
              <option value="video">视频</option>
              <option value="api">API文档</option>
            </select>
          </div>
        )}
      </div>

      {/* 内容区域 */}
      <div>
        {activeTab === 'documents' ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {helpSystem.filteredDocuments.map(doc => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onClick={handleDocumentClick}
                onLike={handleDocumentLike}
              />
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {helpSystem.filteredFAQs.map(faq => (
              <FAQItem
                key={faq.id}
                faq={faq}
                onHelpful={handleFAQHelpful}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * 文档查看器组件
 */
export const DocumentViewer: React.FC<{
  document: HelpDocument
  onBack: () => void
  relatedDocuments: HelpDocument[]
  onRelatedClick: (document: HelpDocument) => void
  className?: string
}> = ({ document, onBack, relatedDocuments, onRelatedClick, className }) => {
  const [showTableOfContents, setShowTableOfContents] = useState(false)

  // 生成目录
  const tableOfContents = useMemo(() => {
    const headings = document.content.match(/^#{1,6}\s+.+$/gm) || []
    return headings.map((heading, index) => {
      const level = (heading.match(/^#+/) || [''])[0].length
      const title = heading.replace(/^#+\s+/, '')
      const id = `heading-${index}`
      
      return { level, title, id }
    })
  }, [document.content])

  return (
    <div className={cn("w-full max-w-4xl mx-auto space-y-6", className)}>
      {/* 头部 */}
      <Card className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ChevronRight className="w-4 h-4 mr-2 rotate-180" />
            返回
          </Button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-foreground">
              {document.title}
            </h1>
            <p className="text-muted-foreground mt-1">
              {document.description}
            </p>
          </div>
        </div>

        {/* 元数据 */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>类型: {document.type}</span>
          <span>难度: {document.difficulty}</span>
          <span>阅读时间: {document.readTime} 分钟</span>
          <span>更新于: {new Date(document.lastUpdated).toLocaleDateString()}</span>
          {document.author && <span>作者: {document.author}</span>}
        </div>

        {/* 标签 */}
        <div className="flex gap-2 mt-3">
          {document.tags.map(tag => (
            <span
              key={tag}
              className="text-xs px-2 py-1 bg-primary/10 text-primary rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      </Card>

      {/* 内容和目录 */}
      <div className="grid gap-6 lg:grid-cols-4">
        {/* 目录 */}
        {tableOfContents.length > 0 && (
          <Card className="lg:col-span-1 p-4 h-fit">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-sm">目录</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowTableOfContents(!showTableOfContents)}
                className="lg:hidden"
              >
                <ChevronDown className={cn(
                  "w-4 h-4 transition-transform",
                  showTableOfContents && "rotate-180"
                )} />
              </Button>
            </div>
            
            <div className={cn(
              "space-y-1",
              !showTableOfContents && "hidden lg:block"
            )}>
              {tableOfContents.map(item => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  className={cn(
                    "block text-sm hover:text-primary transition-colors",
                    `ml-${(item.level - 2) * 4}`
                  )}
                  style={{ marginLeft: `${(item.level - 2) * 16}px` }}
                >
                  {item.title}
                </a>
              ))}
            </div>
          </Card>
        )}

        {/* 文档内容 */}
        <Card className="lg:col-span-3 p-6">
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: document.content }}
          />
        </Card>
      </div>

      {/* 附件 */}
      {document.attachments && document.attachments.length > 0 && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">相关附件</h3>
          <div className="space-y-2">
            {document.attachments.map((attachment, index) => (
              <a
                key={index}
                href={attachment.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 p-3 border rounded-lg hover:bg-muted/50"
              >
                <Download className="w-4 h-4 text-primary" />
                <div className="flex-1">
                  <div className="font-medium text-sm">{attachment.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {attachment.type} • {(attachment.size / 1024).toFixed(1)} KB
                  </div>
                </div>
                <ExternalLink className="w-4 h-4 text-muted-foreground" />
              </a>
            ))}
          </div>
        </Card>
      )}

      {/* 相关文档 */}
      {relatedDocuments.length > 0 && (
        <Card className="p-6">
          <h3 className="font-semibold mb-4">相关文档</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {relatedDocuments.map(doc => (
              <DocumentCard
                key={doc.id}
                document={doc}
                onClick={onRelatedClick}
                showMetadata={false}
              />
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}
