import React, { useState, useCallback, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import {
  Search,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Loader2,
  Copy,
  Globe,
  FileText,
  Calendar,
  User
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ContractLookupProps {
  onContractSelect: (contractData: ContractData) => void;
  className?: string;
}

interface ContractData {
  contractAddress: string;
  network: string;
  isVerified: boolean;
  contractName?: string;
  compilerVersion?: string;
  sourceCode?: string;
  verifiedAt?: string;
  creationTransaction?: string;
  creatorAddress?: string;
  error?: string;
}

const NETWORKS = [
  { value: 'ethereum', label: 'Ethereum', icon: '🔷' },
  { value: 'bsc', label: 'BSC', icon: '🟡' },
  { value: 'polygon', label: 'Polygon', icon: '🟣' },
  { value: 'arbitrum', label: 'Arbitrum', icon: '🔵' },
];

const EXPLORER_URLS = {
  ethereum: 'https://etherscan.io',
  bsc: 'https://bscscan.com',
  polygon: 'https://polygonscan.com',
  arbitrum: 'https://arbiscan.io',
};

export const ContractLookup: React.FC<ContractLookupProps> = ({
  onContractSelect,
  className
}) => {
  const [address, setAddress] = useState('');
  const [network, setNetwork] = useState('ethereum');
  const [loading, setLoading] = useState(false);
  const [contractData, setContractData] = useState<ContractData | null>(null);
  const [searchHistory, setSearchHistory] = useState<ContractData[]>([]);

  // Load search history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('contract-search-history');
    if (saved) {
      try {
        setSearchHistory(JSON.parse(saved));
      } catch (error) {
        console.error('Error loading search history:', error);
      }
    }
  }, []);

  const saveToHistory = (data: ContractData) => {
    const updated = [data, ...searchHistory.filter(h => h.contractAddress !== data.contractAddress)].slice(0, 10);
    setSearchHistory(updated);
    localStorage.setItem('contract-search-history', JSON.stringify(updated));
  };

  const validateAddress = (addr: string) => {
    return /^0x[a-fA-F0-9]{40}$/.test(addr);
  };

  const handleSearch = useCallback(async () => {
    if (!address || !validateAddress(address)) {
      setContractData({
        contractAddress: address,
        network,
        isVerified: false,
        error: 'Invalid contract address format'
      });
      return;
    }

    setLoading(true);
    setContractData(null);

    try {
      const response = await fetch(
        `/api/v1/code-review/contracts/${address}/verify?network=${network}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to verify contract');
      }

      const data = await response.json();
      setContractData(data);
      
      if (data.isVerified) {
        saveToHistory(data);
      }
    } catch (error) {
      setContractData({
        contractAddress: address,
        network,
        isVerified: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setLoading(false);
    }
  }, [address, network]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const openInExplorer = () => {
    if (contractData?.contractAddress) {
      const url = `${EXPLORER_URLS[contractData.network as keyof typeof EXPLORER_URLS]}/address/${contractData.contractAddress}`;
      window.open(url, '_blank');
    }
  };

  const handleHistoryClick = (data: ContractData) => {
    setAddress(data.contractAddress);
    setNetwork(data.network);
    setContractData(data);
  };

  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className={cn('w-full max-w-4xl mx-auto space-y-6', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Contract Address Lookup
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-2">
              <Label htmlFor="contract-address">Contract Address</Label>
              <div className="relative">
                <Input
                  id="contract-address"
                  placeholder="0x..."
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="font-mono pr-10"
                  disabled={loading}
                />
                {address && validateAddress(address) && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                    onClick={() => copyToClipboard(address)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="network">Network</Label>
              <Select value={network} onValueChange={setNetwork} disabled={loading}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {NETWORKS.map((net) => (
                    <SelectItem key={net.value} value={net.value}>
                      <div className="flex items-center gap-2">
                        <span>{net.icon}</span>
                        <span>{net.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleSearch}
            disabled={!address || loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Verifying Contract...
              </>
            ) : (
              <>
                <Search className="h-4 w-4 mr-2" />
                Verify Contract
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Search Results */}
      {contractData && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                {contractData.isVerified ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-500" />
                )}
                Contract Information
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant={contractData.isVerified ? 'default' : 'destructive'}>
                  {contractData.isVerified ? 'Verified' : 'Not Verified'}
                </Badge>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={openInExplorer}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Explorer
                </Button>
                {contractData.isVerified && onContractSelect && (
                  <Button
                    size="sm"
                    onClick={() => onContractSelect(contractData)}
                  >
                    Analyze Contract
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {contractData.error ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{contractData.error}</AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Address</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <code className="text-sm bg-muted px-2 py-1 rounded">
                        {formatAddress(contractData.contractAddress)}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                        onClick={() => copyToClipboard(contractData.contractAddress)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-sm font-medium text-muted-foreground">Network</Label>
                    <div className="flex items-center gap-2 mt-1">
                      <span>{NETWORKS.find(n => n.value === contractData.network)?.icon}</span>
                      <span>{NETWORKS.find(n => n.value === contractData.network)?.label}</span>
                    </div>
                  </div>

                  {contractData.contractName && (
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Contract Name</Label>
                      <p className="mt-1">{contractData.contractName}</p>
                    </div>
                  )}

                  {contractData.compilerVersion && (
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Compiler Version</Label>
                      <p className="mt-1">{contractData.compilerVersion}</p>
                    </div>
                  )}

                  {contractData.verifiedAt && (
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Verified Date</Label>
                      <div className="flex items-center gap-2 mt-1">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span>{formatDate(contractData.verifiedAt)}</span>
                      </div>
                    </div>
                  )}

                  {contractData.creatorAddress && (
                    <div>
                      <Label className="text-sm font-medium text-muted-foreground">Creator</Label>
                      <div className="flex items-center gap-2 mt-1">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <code className="text-sm bg-muted px-2 py-1 rounded">
                          {formatAddress(contractData.creatorAddress)}
                        </code>
                      </div>
                    </div>
                  )}
                </div>

                {contractData.sourceCode && (
                  <>
                    <Separator />
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <Label className="text-sm font-medium text-muted-foreground">
                          Source Code Preview
                        </Label>
                        <Badge variant="secondary">
                          {contractData.sourceCode.split('\n').length} lines
                        </Badge>
                      </div>
                      <div className="bg-muted p-3 rounded-md max-h-40 overflow-y-auto">
                        <pre className="text-xs font-mono">
                          <code>
                            {contractData.sourceCode.split('\n').slice(0, 20).join('\n')}
                            {contractData.sourceCode.split('\n').length > 20 && '\n...'}
                          </code>
                        </pre>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Search History */}
      {searchHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Recent Searches
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {searchHistory.slice(0, 5).map((item, index) => (
                <div
                  key={item.contractAddress}
                  className="flex items-center justify-between p-3 bg-muted rounded-lg cursor-pointer hover:bg-muted/80 transition-colors"
                  onClick={() => handleHistoryClick(item)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-muted-foreground">#{index + 1}</span>
                    <div>
                      <div className="flex items-center gap-2">
                        <code className="text-sm">{formatAddress(item.contractAddress)}</code>
                        <Badge variant={item.isVerified ? 'default' : 'secondary'} className="text-xs">
                          {item.isVerified ? 'Verified' : 'Unverified'}
                        </Badge>
                      </div>
                      {item.contractName && (
                        <p className="text-xs text-muted-foreground">{item.contractName}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>{NETWORKS.find(n => n.value === item.network)?.icon}</span>
                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
