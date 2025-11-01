import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { CodeInput } from './CodeInput';
import { ReviewResults } from './ReviewResults';
import { ContractLookup } from './ContractLookup';
import {
  ArrowRight,
  ArrowLeft,
  Play,
  FileText,
  Search,
  BarChart3,
  CheckCircle,
  AlertCircle,
  Clock,
  Settings,
  Download,
  Share2,
  History
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface CodeReviewWorkflowProps {
  className?: string;
  onAnalysisComplete?: (reviewId: string) => void;
}

type WorkflowStep = 'input' | 'lookup' | 'analysis' | 'results' | 'completed';

interface StepConfig {
  id: WorkflowStep;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  canProceed: boolean;
  isCompleted: boolean;
  isActive: boolean;
}

interface AnalysisSession {
  id: string;
  step: WorkflowStep;
  reviewId?: string;
  contractData?: any;
  analysisData?: any;
  createdAt: string;
}

export const CodeReviewWorkflow: React.FC<CodeReviewWorkflowProps> = ({
  className,
  onAnalysisComplete
}) => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('input');
  const [loading, setLoading] = useState(false);
  const [reviewId, setReviewId] = useState<string>('');
  const [reviewData, setReviewData] = useState<any>(null);
  const [sessions, setSessions] = useState<AnalysisSession[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // Load session history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('code-review-sessions');
    if (saved) {
      try {
        setSessions(JSON.parse(saved));
      } catch (error) {
        console.error('Error loading sessions:', error);
      }
    }
  }, []);

  const saveSession = (session: AnalysisSession) => {
    const updated = [session, ...sessions.filter(s => s.id !== session.id)].slice(0, 20);
    setSessions(updated);
    localStorage.setItem('code-review-sessions', JSON.stringify(updated));
  };

  const workflowSteps: StepConfig[] = [
    {
      id: 'input',
      title: 'Input Code',
      description: 'Paste contract code or upload file',
      icon: FileText,
      canProceed: true,
      isCompleted: currentStep !== 'input',
      isActive: currentStep === 'input'
    },
    {
      id: 'lookup',
      title: 'Contract Lookup',
      description: 'Verify contract address',
      icon: Search,
      canProceed: true,
      isCompleted: ['analysis', 'results', 'completed'].includes(currentStep),
      isActive: currentStep === 'lookup'
    },
    {
      id: 'analysis',
      title: 'Analysis',
      description: 'Running security and quality checks',
      icon: BarChart3,
      canProceed: !!reviewId,
      isCompleted: ['results', 'completed'].includes(currentStep),
      isActive: currentStep === 'analysis'
    },
    {
      id: 'results',
      title: 'Results',
      description: 'Review analysis findings',
      icon: CheckCircle,
      canProceed: !!reviewData,
      isCompleted: currentStep === 'completed',
      isActive: currentStep === 'results'
    },
    {
      id: 'completed',
      title: 'Complete',
      description: 'Analysis finished',
      icon: CheckCircle,
      canProceed: true,
      isCompleted: currentStep === 'completed',
      isActive: currentStep === 'completed'
    }
  ];

  const handleCodeSubmit = async (data: any) => {
    setLoading(true);
    
    try {
      const response = await fetch('/api/v1/code-review/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to start analysis');
      }

      const result = await response.json();
      setReviewId(result.id);
      
      // Save session
      const session: AnalysisSession = {
        id: result.id,
        step: 'analysis',
        reviewId: result.id,
        createdAt: new Date().toISOString()
      };
      saveSession(session);
      
      setCurrentStep('analysis');
      
      // Start polling for results
      pollAnalysisResults(result.id);
      
    } catch (error) {
      console.error('Error starting analysis:', error);
      // Handle error appropriately
    } finally {
      setLoading(false);
    }
  };

  const handleContractSelect = (contractData: any) => {
    // This would typically populate the code input with verified contract
    setCurrentStep('input');
  };

  const pollAnalysisResults = async (id: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/code-review/${id}`);
        if (response.ok) {
          const data = await response.json();
          setReviewData(data);
          
          if (data.status === 'completed') {
            clearInterval(pollInterval);
            setCurrentStep('results');
            onAnalysisComplete?.(id);
          } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            setCurrentStep('results');
          }
        }
      } catch (error) {
        console.error('Error polling results:', error);
      }
    }, 2000);

    // Cleanup after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const handleStepClick = (step: WorkflowStep) => {
    if (step === 'input' || step === 'lookup') {
      setCurrentStep(step);
    } else if (step === 'results' && reviewData) {
      setCurrentStep('results');
    }
  };

  const handleRetry = () => {
    setReviewId('');
    setReviewData(null);
    setCurrentStep('input');
  };

  const handleNewAnalysis = () => {
    setReviewId('');
    setReviewData(null);
    setCurrentStep('input');
  };

  const handleExportReport = async () => {
    if (!reviewId) return;
    
    try {
      const response = await fetch(`/api/v1/code-review/${reviewId}/export`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `code-review-${reviewId}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting report:', error);
    }
  };

  const handleShareResults = async () => {
    if (!reviewId) return;
    
    const shareUrl = `${window.location.origin}/code-review/${reviewId}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Code Review Results',
          text: 'Check out this smart contract security analysis',
          url: shareUrl,
        });
      } catch (error) {
        console.error('Error sharing:', error);
      }
    } else {
      await navigator.clipboard.writeText(shareUrl);
      // Show toast notification
    }
  };

  const getStepProgress = () => {
    const stepIndex = workflowSteps.findIndex(step => step.id === currentStep);
    return ((stepIndex + 1) / workflowSteps.length) * 100;
  };

  return (
    <div className={cn('w-full max-w-6xl mx-auto space-y-6', className)}>
      {/* Workflow Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Code Review Workflow
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Comprehensive smart contract security analysis
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowHistory(!showHistory)}
              >
                <History className="h-4 w-4 mr-2" />
                History ({sessions.length})
              </Button>
              {reviewId && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleExportReport}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleShareResults}
                  >
                    <Share2 className="h-4 w-4 mr-2" />
                    Share
                  </Button>
                </div>
              )}
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Progress</span>
              <span>{Math.round(getStepProgress())}%</span>
            </div>
            <Progress value={getStepProgress()} className="h-2" />
          </div>
        </CardHeader>
        <CardContent>
          {/* Step Navigation */}
          <div className="flex items-center justify-between">
            {workflowSteps.map((step, index) => {
              const Icon = step.icon;
              const isClickable = step.id === 'input' || step.id === 'lookup' || 
                               (step.id === 'results' && reviewData);
              
              return (
                <div
                  key={step.id}
                  className={cn(
                    'flex flex-col items-center space-y-2 cursor-pointer transition-colors',
                    isClickable ? 'hover:text-primary' : 'cursor-not-allowed opacity-50',
                    step.isActive && 'text-primary'
                  )}
                  onClick={() => isClickable && handleStepClick(step.id)}
                >
                  <div className={cn(
                    'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors',
                    step.isCompleted ? 'bg-primary border-primary text-primary-foreground' :
                    step.isActive ? 'border-primary text-primary' :
                    'border-muted text-muted-foreground'
                  )}>
                    {step.isCompleted ? (
                      <CheckCircle className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-medium">{step.title}</p>
                    <p className="text-xs text-muted-foreground hidden md:block">
                      {step.description}
                    </p>
                  </div>
                  
                  {/* Arrow separator */}
                  {index < workflowSteps.length - 1 && (
                    <ArrowRight className="h-4 w-4 text-muted-foreground ml-8 hidden md:block" />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <div className="min-h-[500px]">
        {currentStep === 'input' && (
          <CodeInput
            onSubmit={handleCodeSubmit}
            loading={loading}
          />
        )}

        {currentStep === 'lookup' && (
          <ContractLookup
            onContractSelect={handleContractSelect}
          />
        )}

        {currentStep === 'analysis' && (
          <Card>
            <CardContent className="p-12">
              <div className="text-center space-y-4">
                <div className="animate-spin">
                  <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold">Analysis in Progress</h3>
                <p className="text-muted-foreground">
                  Running comprehensive security and quality checks on your smart contract...
                </p>
                <div className="space-y-2">
                  <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                    <Clock className="h-4 w-4" />
                    This typically takes 30-45 seconds
                  </div>
                  <div className="w-64 mx-auto">
                    <div className="animate-pulse bg-muted h-2 rounded-full" />
                  </div>
                </div>
                <Button variant="outline" onClick={handleNewAnalysis}>
                  Cancel Analysis
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {currentStep === 'results' && (
          <ReviewResults
            reviewId={reviewId}
            reviewData={reviewData}
            onRetry={handleRetry}
          />
        )}

        {currentStep === 'completed' && (
          <Card>
            <CardContent className="p-12">
              <div className="text-center space-y-4">
                <CheckCircle className="h-12 w-12 mx-auto text-green-500" />
                <h3 className="text-lg font-semibold">Analysis Complete</h3>
                <p className="text-muted-foreground">
                  Your smart contract analysis has been completed successfully.
                </p>
                <div className="flex items-center justify-center gap-4">
                  <Button onClick={handleNewAnalysis}>
                    <Play className="h-4 w-4 mr-2" />
                    New Analysis
                  </Button>
                  <Button variant="outline" onClick={handleExportReport}>
                    <Download className="h-4 w-4 mr-2" />
                    Download Report
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Session History */}
      {showHistory && sessions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <History className="h-5 w-5" />
              Recent Analysis Sessions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {sessions.slice(0, 10).map((session) => (
                <div
                  key={session.id}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg cursor-pointer hover:bg-muted/80 transition-colors"
                  onClick={() => {
                    setReviewId(session.reviewId!);
                    setCurrentStep('results');
                    setShowHistory(false);
                  }}
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        {new Date(session.createdAt).toLocaleDateString()}
                      </Badge>
                      <code className="text-sm">{session.id.slice(0, 8)}...</code>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {session.step.replace('_', ' ').toUpperCase()}
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
