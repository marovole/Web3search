import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  FileText,
  Download,
  RefreshCw,
  ExternalLink,
  BarChart3,
  Code,
  Lightbulb
} from 'lucide-react';
import { VulnerabilityList } from './VulnerabilityList';
import { QualityMetrics } from './QualityMetrics';
import { AnalysisProgress } from './AnalysisProgress';
import { cn } from '@/lib/utils';

interface ReviewResultsProps {
  reviewId: string;
  reviewData?: CodeReviewData;
  loading?: boolean;
  onRetry?: () => void;
  className?: string;
}

interface CodeReviewData {
  id: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  contractAddress?: string;
  contractName?: string;
  network: string;
  fileName?: string;
  language: string;
  analysisMode: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  confidenceScore?: number;
  analysisDuration?: number;
  vulnerabilitySummary?: {
    totalVulnerabilities: number;
    severityBreakdown: Record<string, number>;
    highRiskCount: number;
  };
  qualitySummary?: {
    overallScore?: number;
    qualityGrade?: string;
    maintainabilityIndex?: number;
  };
  analysisSummary?: {
    analyzersRun: number;
    totalExecutionTime: number;
    totalTokensUsed: number;
    successfulAnalyses: number;
  };
}

const STATUS_CONFIG = {
  pending: {
    icon: Clock,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-50',
    label: 'Pending',
    description: 'Waiting to start analysis...'
  },
  in_progress: {
    icon: RefreshCw,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50',
    label: 'Analyzing',
    description: 'Analysis in progress...'
  },
  completed: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-50',
    label: 'Completed',
    description: 'Analysis completed successfully'
  },
  failed: {
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-50',
    label: 'Failed',
    description: 'Analysis failed. Please try again.'
  }
};

const SEVERITY_COLORS = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-blue-500',
  info: 'bg-gray-500'
};

export const ReviewResults: React.FC<ReviewResultsProps> = ({
  reviewId,
  reviewData,
  loading = false,
  onRetry,
  className
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [progressData, setProgressData] = useState<any>(null);

  const status = reviewData?.status || 'pending';
  const statusConfig = STATUS_CONFIG[status];
  const StatusIcon = statusConfig.icon;

  useEffect(() => {
    if (status === 'in_progress' && !progressData) {
      // Set up SSE connection for real-time progress
      const eventSource = new EventSource(`/api/v1/code-review/${reviewId}/stream`);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setProgressData(data);
          
          if (data.status === 'completed' || data.status === 'failed') {
            eventSource.close();
            // Trigger a refresh of the review data
            window.location.reload();
          }
        } catch (error) {
          console.error('Error parsing SSE data:', error);
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
      };
      
      return () => {
        eventSource.close();
      };
    }
  }, [status, reviewId, progressData]);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  };

  const getGradeColor = (grade?: string) => {
    if (!grade) return 'text-gray-500';
    if (grade.startsWith('A')) return 'text-green-600';
    if (grade.startsWith('B')) return 'text-blue-600';
    if (grade.startsWith('C')) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskLevel = (highRiskCount?: number) => {
    if (!highRiskCount) return { level: 'Low', color: 'text-green-600' };
    if (highRiskCount >= 5) return { level: 'Critical', color: 'text-red-600' };
    if (highRiskCount >= 3) return { level: 'High', color: 'text-orange-600' };
    if (highRiskCount >= 1) return { level: 'Medium', color: 'text-yellow-600' };
    return { level: 'Low', color: 'text-green-600' };
  };

  const riskLevel = getRiskLevel(reviewData?.vulnerabilitySummary?.highRiskCount);

  if (loading && !reviewData) {
    return (
      <Card className={cn('w-full max-w-6xl mx-auto', className)}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center py-12">
            <div className="text-center space-y-4">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
              <p className="text-muted-foreground">Loading review results...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('w-full max-w-6xl mx-auto space-y-6', className)}>
      {/* Status Header */}
      <Card className={statusConfig.bgColor}>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <StatusIcon className={cn('h-6 w-6', statusConfig.color)} />
              <div>
                <CardTitle className={statusConfig.color}>{statusConfig.label}</CardTitle>
                <p className="text-sm text-muted-foreground">{statusConfig.description}</p>
              </div>
            </div>
            
            {status === 'failed' && onRetry && (
              <Button variant="outline" onClick={onRetry} size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Retry Analysis
              </Button>
            )}
          </div>
        </CardHeader>
      </Card>

      {status === 'in_progress' && (
        <AnalysisProgress progressData={progressData} />
      )}

      {status === 'completed' && reviewData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Risk Level</p>
                    <p className={cn('text-lg font-semibold', riskLevel.color)}>
                      {riskLevel.level}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Vulnerabilities</p>
                    <p className="text-lg font-semibold">
                      {reviewData.vulnerabilitySummary?.totalVulnerabilities || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Quality Score</p>
                    <p className={cn('text-lg font-semibold', getGradeColor(reviewData.qualitySummary?.qualityGrade))}>
                      {reviewData.qualitySummary?.qualityGrade || 'N/A'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Analysis Time</p>
                    <p className="text-lg font-semibold">
                      {formatDuration(reviewData.analysisDuration)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Results */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Analysis Results</CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    Confidence: {((reviewData.confidenceScore || 0) * 100).toFixed(1)}%
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export Report
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="overview" className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Overview
                  </TabsTrigger>
                  <TabsTrigger value="vulnerabilities" className="flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    Security
                  </TabsTrigger>
                  <TabsTrigger value="quality" className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4" />
                    Quality
                  </TabsTrigger>
                  <TabsTrigger value="code" className="flex items-center gap-2">
                    <Code className="h-4 w-4" />
                    Code
                  </TabsTrigger>
                  <TabsTrigger value="recommendations" className="flex items-center gap-2">
                    <Lightbulb className="h-4 w-4" />
                    Fixes
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Security Overview</h3>
                      <div className="space-y-3">
                        {Object.entries(reviewData.vulnerabilitySummary?.severityBreakdown || {}).map(([severity, count]) => (
                          <div key={severity} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className={cn('w-3 h-3 rounded-full', SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS])} />
                              <span className="capitalize">{severity}</span>
                            </div>
                            <Badge variant="secondary">{count}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-semibold mb-4">Quality Metrics</h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span>Overall Score</span>
                          <span className={cn('font-semibold', getGradeColor(reviewData.qualitySummary?.qualityGrade))}>
                            {reviewData.qualitySummary?.overallScore || 0}/100
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Maintainability</span>
                          <span className="font-semibold">
                            {reviewData.qualitySummary?.maintainabilityIndex?.toFixed(1) || 'N/A'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Analysis Mode</span>
                          <Badge variant="outline">{reviewData.analysisMode}</Badge>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator />

                  <div>
                    <h3 className="text-lg font-semibold mb-4">Analysis Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <p className="text-2xl font-bold">{reviewData.analysisSummary?.analyzersRun || 0}</p>
                        <p className="text-sm text-muted-foreground">Analyzers Run</p>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <p className="text-2xl font-bold">{reviewData.analysisSummary?.totalTokensUsed || 0}</p>
                        <p className="text-sm text-muted-foreground">Tokens Used</p>
                      </div>
                      <div className="text-center p-4 bg-muted rounded-lg">
                        <p className="text-2xl font-bold">{reviewData.analysisSummary?.successfulAnalyses || 0}</p>
                        <p className="text-sm text-muted-foreground">Successful</p>
                      </div>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="vulnerabilities">
                  <VulnerabilityList reviewId={reviewId} />
                </TabsContent>

                <TabsContent value="quality">
                  <QualityMetrics reviewId={reviewId} />
                </TabsContent>

                <TabsContent value="code">
                  <div className="space-y-4">
                    <Alert>
                      <FileText className="h-4 w-4" />
                      <AlertDescription>
                        Source code viewer with vulnerability highlighting and inline fixes.
                      </AlertDescription>
                    </Alert>
                    <p className="text-muted-foreground">Code viewer component will be implemented here.</p>
                  </div>
                </TabsContent>

                <TabsContent value="recommendations">
                  <div className="space-y-4">
                    <Alert>
                      <Lightbulb className="h-4 w-4" />
                      <AlertDescription>
                        AI-powered fix recommendations and best practices.
                      </AlertDescription>
                    </Alert>
                    <p className="text-muted-foreground">Recommendations component will be implemented here.</p>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
};
