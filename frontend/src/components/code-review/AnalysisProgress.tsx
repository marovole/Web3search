import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import {
  Code,
  Search,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Loader2
} from 'lucide-react';

interface AnalysisProgressProps {
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  currentStep?: string;
  progress?: number;
  estimatedTime?: number;
  className?: string;
}

interface AnalysisStep {
  id: string;
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  icon: React.ReactNode;
  description?: string;
}

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  status,
  currentStep,
  progress = 0,
  estimatedTime,
  className
}) => {
  const [steps, setSteps] = useState<AnalysisStep[]>([
    {
      id: 'parsing',
      name: 'Code Parsing',
      status: 'pending',
      icon: <Code className="h-4 w-4" />,
      description: 'Analyzing code structure and syntax'
    },
    {
      id: 'security',
      name: 'Security Analysis',
      status: 'pending',
      icon: <Shield className="h-4 w-4" />,
      description: 'Scanning for security vulnerabilities'
    },
    {
      id: 'vulnerabilities',
      name: 'Vulnerability Detection',
      status: 'pending',
      icon: <AlertTriangle className="h-4 w-4" />,
      description: 'Identifying potential vulnerabilities'
    },
    {
      id: 'optimization',
      name: 'Optimization Analysis',
      status: 'pending',
      icon: <Search className="h-4 w-4" />,
      description: 'Analyzing performance and gas optimization'
    }
  ]);

  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    if (status === 'in_progress' && currentStep) {
      const stepIndex = steps.findIndex(step => step.id === currentStep);
      if (stepIndex !== -1) {
        setCurrentStepIndex(stepIndex);
        
        setSteps(prevSteps => 
          prevSteps.map((step, index) => ({
            ...step,
            status: index < stepIndex ? 'completed' : 
                   index === stepIndex ? 'in_progress' : 'pending'
          }))
        );
      }
    } else if (status === 'completed') {
      setSteps(prevSteps => 
        prevSteps.map(step => ({ ...step, status: 'completed' }))
      );
    } else if (status === 'failed') {
      setSteps(prevSteps => 
        prevSteps.map((step, index) => ({
          ...step,
          status: index < currentStepIndex ? 'completed' : 
                 index === currentStepIndex ? 'failed' : 'pending'
        }))
      );
    }
  }, [status, currentStep, currentStepIndex, steps.length]);

  const getStatusBadgeVariant = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed': return 'default';
      case 'in_progress': return 'secondary';
      case 'failed': return 'destructive';
      default: return 'outline';
    }
  };

  const getStatusText = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed': return 'Completed';
      case 'in_progress': return 'In Progress';
      case 'failed': return 'Failed';
      default: return 'Pending';
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {status === 'in_progress' ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : status === 'completed' ? (
            <CheckCircle className="h-5 w-5 text-green-600" />
          ) : status === 'failed' ? (
            <AlertTriangle className="h-5 w-5 text-red-600" />
          ) : (
            <Clock className="h-5 w-5" />
          )}
          Analysis Progress
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overall Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Overall Progress</span>
            <span className="text-sm text-muted-foreground">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
          {estimatedTime && status === 'in_progress' && (
            <p className="text-xs text-muted-foreground">
              Estimated time remaining: {formatTime(estimatedTime)}
            </p>
          )}
        </div>

        <Separator />

        {/* Step-by-step Progress */}
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={step.id} className="flex items-start gap-3">
              <div className="flex-shrink-0">
                <div className={cn(
                  "flex items-center justify-center w-8 h-8 rounded-full border-2",
                  step.status === 'completed' && "border-green-600 bg-green-600 text-white",
                  step.status === 'in_progress' && "border-blue-600 bg-blue-600 text-white",
                  step.status === 'failed' && "border-red-600 bg-red-600 text-white",
                  step.status === 'pending' && "border-gray-300 bg-gray-100 text-gray-500"
                )}>
                  {step.status === 'completed' ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : step.status === 'failed' ? (
                    <AlertTriangle className="h-4 w-4" />
                  ) : step.status === 'in_progress' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    step.icon
                  )}
                </div>
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-medium">{step.name}</h4>
                  <Badge variant={getStatusBadgeVariant(step.status)} className="text-xs">
                    {getStatusText(step.status)}
                  </Badge>
                </div>
                {step.description && (
                  <p className="text-xs text-muted-foreground mb-2">{step.description}</p>
                )}
                {step.status === 'in_progress' && (
                  <Progress value={progress} className="h-1" />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Status Message */}
        {status === 'failed' && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">
              Analysis failed. Please check your code and try again.
            </p>
          </div>
        )}
        
        {status === 'completed' && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md">
            <p className="text-sm text-green-800">
              Analysis completed successfully! View the results below.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
