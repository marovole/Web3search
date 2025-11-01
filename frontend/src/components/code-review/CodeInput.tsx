import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Upload, FileText, Link, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CodeInputProps {
  onSubmit: (data: CodeSubmissionData) => void;
  loading?: boolean;
  className?: string;
}

interface CodeSubmissionData {
  sourceCode?: string;
  contractAddress?: string;
  network: string;
  contractName?: string;
  fileName: string;
  language: string;
  analysisMode: 'quick' | 'thorough';
}

const SUPPORTED_NETWORKS = [
  { value: 'ethereum', label: 'Ethereum', description: 'ETH Mainnet' },
  { value: 'bsc', label: 'BSC', description: 'Binance Smart Chain' },
  { value: 'polygon', label: 'Polygon', description: 'Polygon Mainnet' },
  { value: 'arbitrum', label: 'Arbitrum', description: 'Arbitrum One' },
];

const LANGUAGES = [
  { value: 'solidity', label: 'Solidity' },
  { value: 'rust', label: 'Rust (Solana)' },
  { value: 'vyper', label: 'Vyper' },
];

const ANALYSIS_MODES = [
  { value: 'quick', label: 'Quick', description: 'Fast analysis (~10s)' },
  { value: 'thorough', label: 'Thorough', description: 'Comprehensive analysis (~45s)' },
];

export const CodeInput: React.FC<CodeInputProps> = ({
  onSubmit,
  loading = false,
  className
}) => {
  const [activeTab, setActiveTab] = useState<'code' | 'address'>('code');
  const [sourceCode, setSourceCode] = useState('');
  const [contractAddress, setContractAddress] = useState('');
  const [contractName, setContractName] = useState('');
  const [fileName, setFileName] = useState('contract.sol');
  const [network, setNetwork] = useState('ethereum');
  const [language, setLanguage] = useState('solidity');
  const [analysisMode, setAnalysisMode] = useState<'quick' | 'thorough'>('thorough');
  const [addressValidation, setAddressValidation] = useState<{
    isValid: boolean;
    isVerified: boolean;
    contractName?: string;
    loading: boolean;
  }>({ isValid: false, isVerified: false, loading: false });

  const validateAddress = useCallback(async (address: string) => {
    if (!address || address.length !== 42 || !address.startsWith('0x')) {
      setAddressValidation({ isValid: false, isVerified: false, loading: false });
      return;
    }

    setAddressValidation(prev => ({ ...prev, loading: true }));

    try {
      const response = await fetch(`/api/v1/code-review/contracts/${address}/verify?network=${network}`);
      const data = await response.json();

      if (data.is_verified) {
        setAddressValidation({
          isValid: true,
          isVerified: true,
          contractName: data.contract_name,
          loading: false
        });
        
        // Auto-fill contract name if available
        if (data.contract_name && !contractName) {
          setContractName(data.contract_name);
        }
      } else {
        setAddressValidation({
          isValid: true,
          isVerified: false,
          loading: false
        });
      }
    } catch (error) {
      setAddressValidation({
        isValid: false,
        isVerified: false,
        loading: false
      });
    }
  }, [network, contractName]);

  const handleAddressChange = (value: string) => {
    setContractAddress(value);
    if (value.length === 42) {
      validateAddress(value);
    } else {
      setAddressValidation({ isValid: false, isVerified: false, loading: false });
    }
  };

  const handleSubmit = () => {
    const submissionData: CodeSubmissionData = {
      network,
      fileName,
      language,
      analysisMode,
    };

    if (activeTab === 'code') {
      if (!sourceCode.trim()) {
        return;
      }
      submissionData.sourceCode = sourceCode;
      submissionData.contractName = contractName || undefined;
    } else {
      if (!contractAddress || !addressValidation.isValid) {
        return;
      }
      submissionData.contractAddress = contractAddress;
      submissionData.contractName = contractName || addressValidation.contractName;
    }

    onSubmit(submissionData);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        setSourceCode(content);
        setFileName(file.name);
        
        // Auto-detect language from file extension
        const extension = file.name.split('.').pop()?.toLowerCase();
        if (extension === 'sol') {
          setLanguage('solidity');
        } else if (extension === 'rs') {
          setLanguage('rust');
        } else if (extension === 'vy') {
          setLanguage('vyper');
        }
      };
      reader.readAsText(file);
    }
  };

  const isFormValid = () => {
    if (activeTab === 'code') {
      return sourceCode.trim().length > 0;
    } else {
      return contractAddress.length === 42 && addressValidation.isValid;
    }
  };

  return (
    <Card className={cn('w-full max-w-4xl mx-auto', className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Smart Contract Code Review
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'code' | 'address')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="code" className="flex items-center gap-2">
              <Upload className="h-4 w-4" />
              Paste Code
            </TabsTrigger>
            <TabsTrigger value="address" className="flex items-center gap-2">
              <Link className="h-4 w-4" />
              Contract Address
            </TabsTrigger>
          </TabsList>

          <TabsContent value="code" className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="source-code">Source Code</Label>
                <div className="flex items-center gap-2">
                  <input
                    type="file"
                    accept=".sol,.rs,.vy"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="file-upload"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => document.getElementById('file-upload')?.click()}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Upload File
                  </Button>
                  {fileName !== 'contract.sol' && (
                    <Badge variant="secondary">{fileName}</Badge>
                  )}
                </div>
              </div>
              <Textarea
                id="source-code"
                placeholder="Paste your smart contract source code here..."
                value={sourceCode}
                onChange={(e) => setSourceCode(e.target.value)}
                className="min-h-[300px] font-mono text-sm"
                disabled={loading}
              />
              <div className="text-xs text-muted-foreground">
                {sourceCode.length} characters • {sourceCode.split('\n').length} lines
              </div>
            </div>
          </TabsContent>

          <TabsContent value="address" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="contract-address">Contract Address</Label>
              <div className="relative">
                <Input
                  id="contract-address"
                  placeholder="0x..."
                  value={contractAddress}
                  onChange={(e) => handleAddressChange(e.target.value)}
                  className="font-mono"
                  disabled={loading}
                />
                {addressValidation.loading && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                )}
                {addressValidation.isValid && (
                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                    {addressValidation.isVerified ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-yellow-500" />
                    )}
                  </div>
                )}
              </div>
              
              {contractAddress.length === 42 && (
                <div className="space-y-2">
                  {addressValidation.isVerified ? (
                    <Alert>
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Contract is verified on {network}. 
                        {addressValidation.contractName && ` Name: ${addressValidation.contractName}`}
                      </AlertDescription>
                    </Alert>
                  ) : addressValidation.isValid ? (
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Contract found but source code is not verified. You may need to provide the source code manually.
                      </AlertDescription>
                    </Alert>
                  ) : contractAddress.length > 0 ? (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        Invalid contract address format.
                      </AlertDescription>
                    </Alert>
                  ) : null}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-2">
            <Label htmlFor="network">Network</Label>
            <Select value={network} onValueChange={setNetwork} disabled={loading}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SUPPORTED_NETWORKS.map((net) => (
                  <SelectItem key={net.value} value={net.value}>
                    <div>
                      <div className="font-medium">{net.label}</div>
                      <div className="text-sm text-muted-foreground">{net.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Select value={language} onValueChange={setLanguage} disabled={loading}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {LANGUAGES.map((lang) => (
                  <SelectItem key={lang.value} value={lang.value}>
                    {lang.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="analysis-mode">Analysis Mode</Label>
            <Select value={analysisMode} onValueChange={(value: 'quick' | 'thorough') => setAnalysisMode(value)} disabled={loading}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ANALYSIS_MODES.map((mode) => (
                  <SelectItem key={mode.value} value={mode.value}>
                    <div>
                      <div className="font-medium">{mode.label}</div>
                      <div className="text-sm text-muted-foreground">{mode.description}</div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="contract-name">Contract Name (Optional)</Label>
            <Input
              id="contract-name"
              placeholder="MyContract"
              value={contractName}
              onChange={(e) => setContractName(e.target.value)}
              disabled={loading}
            />
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid() || loading}
            size="lg"
            className="min-w-[120px]"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Start Analysis'
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
