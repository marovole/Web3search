import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import {
  Shield,
  Code,
  Zap,
  AlertTriangle,
  CheckCircle,
  BarChart3
} from 'lucide-react';

interface QualityMetricsProps {
  metrics?: {
    overallScore?: number;
    securityScore?: number;
    performanceScore?: number;
    readabilityScore?: number;
    maintainabilityScore?: number;
    complexity?: number;
    linesOfCode?: number;
    testCoverage?: number;
  };
  className?: string;
}

export const QualityMetrics: React.FC<QualityMetricsProps> = ({ 
  metrics, 
  className 
}) => {
  if (!metrics) {
    return null;
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score: number): "default" | "secondary" | "destructive" | "outline" => {
    if (score >= 80) return 'default';
    if (score >= 60) return 'secondary';
    return 'destructive';
  };

  const formatScore = (score?: number) => {
    if (score === undefined) return 'N/A';
    return `${Math.round(score)}%`;
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Quality Metrics
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Score */}
        <div className="text-center">
          <div className={`text-4xl font-bold ${getScoreColor(metrics.overallScore || 0)}`}>
            {formatScore(metrics.overallScore)}
          </div>
          <p className="text-sm text-muted-foreground">Overall Quality Score</p>
        </div>

        <Separator />

        {/* Individual Scores */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                <span className="text-sm font-medium">Security</span>
              </div>
              <Badge variant={getScoreBadgeVariant(metrics.securityScore || 0)}>
                {formatScore(metrics.securityScore)}
              </Badge>
            </div>
            <Progress value={metrics.securityScore || 0} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                <span className="text-sm font-medium">Performance</span>
              </div>
              <Badge variant={getScoreBadgeVariant(metrics.performanceScore || 0)}>
                {formatScore(metrics.performanceScore)}
              </Badge>
            </div>
            <Progress value={metrics.performanceScore || 0} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code className="h-4 w-4" />
                <span className="text-sm font-medium">Readability</span>
              </div>
              <Badge variant={getScoreBadgeVariant(metrics.readabilityScore || 0)}>
                {formatScore(metrics.readabilityScore)}
              </Badge>
            </div>
            <Progress value={metrics.readabilityScore || 0} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm font-medium">Maintainability</span>
              </div>
              <Badge variant={getScoreBadgeVariant(metrics.maintainabilityScore || 0)}>
                {formatScore(metrics.maintainabilityScore)}
              </Badge>
            </div>
            <Progress value={metrics.maintainabilityScore || 0} className="h-2" />
          </div>
        </div>

        <Separator />

        {/* Additional Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold">{metrics.linesOfCode || 'N/A'}</div>
            <p className="text-xs text-muted-foreground">Lines of Code</p>
          </div>
          <div>
            <div className="text-2xl font-bold">{metrics.complexity || 'N/A'}</div>
            <p className="text-xs text-muted-foreground">Complexity</p>
          </div>
          <div>
            <div className="text-2xl font-bold">{formatScore(metrics.testCoverage)}</div>
            <p className="text-xs text-muted-foreground">Test Coverage</p>
          </div>
          <div>
            <div className={`text-2xl font-bold ${getScoreColor(metrics.overallScore || 0)}`}>
              {metrics.overallScore && metrics.overallScore >= 80 ? 'A' : 
               metrics.overallScore && metrics.overallScore >= 60 ? 'B' : 'C'}
            </div>
            <p className="text-xs text-muted-foreground">Grade</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
