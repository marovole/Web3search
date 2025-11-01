"""
Performance Optimizer for Large Contract Analysis
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime
import hashlib
import zlib
from dataclasses import dataclass

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


@dataclass
class ContractChunk:
    """Represents a chunk of contract code for analysis"""
    id: str
    content: str
    start_line: int
    end_line: int
    functions: List[str]
    size_bytes: int


class PerformanceOptimizer:
    """Optimizes analysis performance for large smart contracts"""
    
    def __init__(self):
        self.max_contract_size = 100_000  # 100KB
        self.chunk_size = 10_000  # 10KB chunks
        self.max_functions_per_chunk = 20
        self.compression_threshold = 50_000  # Compress contracts larger than 50KB
        
    async def optimize_contract_for_analysis(
        self, 
        source_code: str, 
        analysis_mode: str = "thorough"
    ) -> Dict[str, Any]:
        """
        Optimize contract code for efficient analysis
        
        Args:
            source_code: Raw contract source code
            analysis_mode: Analysis mode (quick or thorough)
            
        Returns:
            Optimization metadata and processed code
        """
        
        # Calculate contract metrics
        contract_size = len(source_code.encode('utf-8'))
        line_count = len(source_code.split('\n'))
        function_count = self._count_functions(source_code)
        
        # Generate contract hash for caching
        contract_hash = hashlib.sha256(source_code.encode()).hexdigest()
        
        # Check cache first
        cache_key = f"optimized_contract:{contract_hash}:{analysis_mode}"
        cached_result = await redis_client.get(cache_key)
        
        if cached_result:
            logger.info(f"Using cached optimized contract for hash {contract_hash[:8]}")
            return cached_result
        
        # Determine optimization strategy
        optimization_strategy = self._determine_strategy(
            contract_size, line_count, function_count, analysis_mode
        )
        
        # Apply optimizations
        optimized_data = await self._apply_optimizations(
            source_code, optimization_strategy, contract_hash
        )
        
        # Add metadata
        optimized_data.update({
            "original_size": contract_size,
            "original_lines": line_count,
            "original_functions": function_count,
            "optimization_strategy": optimization_strategy,
            "contract_hash": contract_hash,
            "optimized_at": datetime.utcnow().isoformat()
        })
        
        # Cache result for 24 hours
        await redis_client.setex(cache_key, 86400, optimized_data)
        
        return optimized_data
    
    def _determine_strategy(
        self, 
        size: int, 
        lines: int, 
        functions: int, 
        mode: str
    ) -> str:
        """Determine the best optimization strategy"""
        
        if mode == "quick":
            if size > 50_000:
                return "chunk_quick"
            elif functions > 50:
                return "function_sampling_quick"
            else:
                return "minimal_quick"
        else:  # thorough
            if size > self.max_contract_size:
                return "chunk_thorough"
            elif functions > 100:
                return "function_sampling_thorough"
            elif size > self.compression_threshold:
                return "compression_thorough"
            else:
                return "standard_thorough"
    
    async def _apply_optimizations(
        self, 
        source_code: str, 
        strategy: str, 
        contract_hash: str
    ) -> Dict[str, Any]:
        """Apply the chosen optimization strategy"""
        
        if strategy.startswith("chunk"):
            return await self._chunk_contract(source_code, strategy)
        elif strategy.startswith("function_sampling"):
            return await self._sample_functions(source_code, strategy)
        elif strategy.startswith("compression"):
            return await self._compress_contract(source_code, strategy)
        elif strategy.startswith("minimal"):
            return await self._minimal_processing(source_code, strategy)
        else:
            return await self._standard_processing(source_code, strategy)
    
    async def _chunk_contract(self, source_code: str, strategy: str) -> Dict[str, Any]:
        """Split large contract into manageable chunks"""
        
        chunks = self._create_chunks(source_code)
        
        # For quick mode, only analyze critical chunks
        if "quick" in strategy:
            chunks = self._prioritize_chunks(chunks)[:3]  # Top 3 chunks
        
        return {
            "strategy": "chunking",
            "chunks": [self._serialize_chunk(chunk) for chunk in chunks],
            "total_chunks": len(chunks),
            "requires_merging": True,
            "analysis_parallel": "thorough" not in strategy
        }
    
    async def _sample_functions(self, source_code: str, strategy: str) -> Dict[str, Any]:
        """Sample representative functions for analysis"""
        
        functions = self._extract_functions(source_code)
        
        # Prioritize functions by complexity and importance
        prioritized_functions = self._prioritize_functions(functions)
        
        # Limit number of functions based on mode
        max_functions = 10 if "quick" in strategy else 25
        selected_functions = prioritized_functions[:max_functions]
        
        # Reconstruct contract with selected functions
        optimized_code = self._reconstruct_with_functions(source_code, selected_functions)
        
        return {
            "strategy": "function_sampling",
            "optimized_code": optimized_code,
            "selected_functions": [f["name"] for f in selected_functions],
            "total_functions": len(functions),
            "sampled_functions": len(selected_functions),
            "requires_merging": False
        }
    
    async def _compress_contract(self, source_code: str, strategy: str) -> Dict[str, Any]:
        """Compress contract while preserving analyzable content"""
        
        # Remove comments and whitespace for analysis
        compressed_code = self._remove_comments_and_whitespace(source_code)
        
        # Compress data for storage/transmission
        compressed_data = zlib.compress(compressed_code.encode('utf-8'))
        
        return {
            "strategy": "compression",
            "compressed_code": compressed_code.hex(),
            "compressed_size": len(compressed_data),
            "compression_ratio": len(compressed_data) / len(source_code.encode('utf-8')),
            "requires_decompression": True,
            "original_code_hash": hashlib.sha256(source_code.encode()).hexdigest()
        }
    
    async def _minimal_processing(self, source_code: str, strategy: str) -> Dict[str, Any]:
        """Minimal processing for quick analysis"""
        
        # Extract only function signatures and critical areas
        critical_areas = self._extract_critical_areas(source_code)
        
        return {
            "strategy": "minimal",
            "critical_areas": critical_areas,
            "requires_merging": False,
            "focus_areas": ["function_signatures", "external_calls", "state_changes"]
        }
    
    async def _standard_processing(self, source_code: str, strategy: str) -> Dict[str, Any]:
        """Standard processing without major optimizations"""
        
        return {
            "strategy": "standard",
            "processed_code": source_code,
            "requires_merging": False,
            "optimizations_applied": ["basic_cleanup"]
        }
    
    def _create_chunks(self, source_code: str) -> List[ContractChunk]:
        """Create chunks from contract source code"""
        
        lines = source_code.split('\n')
        chunks = []
        
        current_chunk_lines = []
        current_chunk_functions = []
        current_start_line = 0
        
        for i, line in enumerate(lines):
            current_chunk_lines.append(line)
            
            # Track functions in current chunk
            if self._is_function_definition(line):
                func_name = self._extract_function_name(line)
                if func_name:
                    current_chunk_functions.append(func_name)
            
            # Create chunk when size limit reached or at function boundaries
            chunk_size = len('\n'.join(current_chunk_lines).encode('utf-8'))
            
            if (chunk_size >= self.chunk_size or 
                len(current_chunk_functions) >= self.max_functions_per_chunk or
                i == len(lines) - 1):
                
                chunk = ContractChunk(
                    id=f"chunk_{len(chunks)}",
                    content='\n'.join(current_chunk_lines),
                    start_line=current_start_line,
                    end_line=i,
                    functions=current_chunk_functions.copy(),
                    size_bytes=chunk_size
                )
                
                chunks.append(chunk)
                current_chunk_lines = []
                current_chunk_functions = []
                current_start_line = i + 1
        
        return chunks
    
    def _prioritize_chunks(self, chunks: List[ContractChunk]) -> List[ContractChunk]:
        """Prioritize chunks based on likely vulnerability density"""
        
        # Score chunks based on various factors
        scored_chunks = []
        
        for chunk in chunks:
            score = 0
            
            # More functions = higher complexity
            score += len(chunk.functions) * 2
            
            # Check for vulnerability indicators
            content_lower = chunk.content.lower()
            
            # High-risk patterns
            high_risk_patterns = [
                'call{value:', '.call(', 'delegatecall', 'selfdestruct',
                'require(', 'assert(', 'while(', 'for('
            ]
            
            for pattern in high_risk_patterns:
                score += content_lower.count(pattern) * 3
            
            # External calls and state changes
            score += content_lower.count('msg.sender') * 2
            score += content_lower.count('transfer(') * 2
            score += content_lower.count('send(') * 2
            
            scored_chunks.append((chunk, score))
        
        # Sort by score (descending)
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return [chunk for chunk, score in scored_chunks]
    
    def _extract_functions(self, source_code: str) -> List[Dict[str, Any]]:
        """Extract function information from source code"""
        
        import re
        
        function_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*(public|private|external|internal)?\s*(view|pure|payable)?\s*(returns\s*\([^)]*\))?\s*\{'
        
        functions = []
        lines = source_code.split('\n')
        
        for match in re.finditer(function_pattern, source_code, re.MULTILINE):
            func_name = match.group(1)
            visibility = match.group(2) or "internal"
            mutability = match.group(3) or ""
            
            # Find function start and end
            start_pos = match.start()
            line_num = source_code[:start_pos].count('\n')
            
            # Calculate function complexity (simplified)
            func_content = source_code[start_pos:start_pos + 2000]  # Look ahead 2k chars
            complexity = func_content.count('if') + func_content.count('for') + func_content.count('while')
            
            functions.append({
                "name": func_name,
                "visibility": visibility,
                "mutability": mutability,
                "line_number": line_num,
                "complexity": complexity,
                "is_external": visibility in ["public", "external"],
                "is_payable": mutability == "payable"
            })
        
        return functions
    
    def _prioritize_functions(self, functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize functions for analysis"""
        
        # Score functions based on risk factors
        scored_functions = []
        
        for func in functions:
            score = 0
            
            # External and payable functions are higher risk
            if func["is_external"]:
                score += 5
            if func["is_payable"]:
                score += 10
            
            # Higher complexity = more potential issues
            score += func["complexity"]
            
            # Public functions that modify state are important
            if func["is_external"] and func["mutability"] not in ["view", "pure"]:
                score += 3
            
            scored_functions.append((func, score))
        
        # Sort by score (descending)
        scored_functions.sort(key=lambda x: x[1], reverse=True)
        
        return [func for func, score in scored_functions]
    
    def _reconstruct_with_functions(
        self, 
        source_code: str, 
        selected_functions: List[Dict[str, Any]]
    ) -> str:
        """Reconstruct contract with only selected functions"""
        
        lines = source_code.split('\n')
        selected_func_names = {f["name"] for f in selected_functions}
        
        reconstructed_lines = []
        current_function = None
        in_selected_function = False
        brace_count = 0
        
        for line in lines:
            # Check if this is a function definition
            if self._is_function_definition(line):
                func_name = self._extract_function_name(line)
                current_function = func_name
                in_selected_function = func_name in selected_func_names
                brace_count = 0
            
            # Include line if we're in a selected function or it's not a function line
            if in_selected_function or not current_function:
                reconstructed_lines.append(line)
                
                # Track braces to know when function ends
                if current_function and in_selected_function:
                    brace_count += line.count('{') - line.count('}')
                    if brace_count <= 0:
                        current_function = None
                        in_selected_function = False
        
        return '\n'.join(reconstructed_lines)
    
    def _remove_comments_and_whitespace(self, source_code: str) -> str:
        """Remove comments and excess whitespace"""
        
        import re
        
        # Remove single-line comments
        code = re.sub(r'//.*', '', source_code)
        
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Remove excess whitespace
        code = re.sub(r'\s+', ' ', code)
        code = code.strip()
        
        return code
    
    def _extract_critical_areas(self, source_code: str) -> List[Dict[str, Any]]:
        """Extract critical areas for quick analysis"""
        
        areas = []
        lines = source_code.split('\n')
        
        # Look for function definitions
        for i, line in enumerate(lines):
            if self._is_function_definition(line):
                func_name = self._extract_function_name(line)
                
                # Extract function signature
                areas.append({
                    "type": "function_signature",
                    "line_number": i,
                    "content": line.strip(),
                    "function_name": func_name
                })
        
        # Look for external calls
        for i, line in enumerate(lines):
            if any(pattern in line for pattern in ['.call(', '.send(', '.transfer(', 'delegatecall']):
                areas.append({
                    "type": "external_call",
                    "line_number": i,
                    "content": line.strip()
                })
        
        return areas
    
    def _serialize_chunk(self, chunk: ContractChunk) -> Dict[str, Any]:
        """Serialize chunk for storage/transmission"""
        
        return {
            "id": chunk.id,
            "content": chunk.content,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "functions": chunk.functions,
            "size_bytes": chunk.size_bytes
        }
    
    def _count_functions(self, source_code: str) -> int:
        """Count functions in source code"""
        return len(self._extract_functions(source_code))
    
    def _is_function_definition(self, line: str) -> bool:
        """Check if line contains a function definition"""
        import re
        pattern = r'function\s+\w+\s*\([^)]*\)'
        return bool(re.search(pattern, line))
    
    def _extract_function_name(self, line: str) -> Optional[str]:
        """Extract function name from definition line"""
        import re
        match = re.search(r'function\s+(\w+)\s*\(', line)
        return match.group(1) if match else None
    
    async def merge_chunk_results(
        self, 
        chunk_results: List[Dict[str, Any]], 
        original_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge results from chunked analysis"""
        
        merged_vulnerabilities = []
        merged_metrics = {}
        total_execution_time = 0
        total_tokens_used = 0
        
        for result in chunk_results:
            # Merge vulnerabilities
            if "vulnerabilities" in result:
                chunk_vulns = result["vulnerabilities"]
                
                # Adjust line numbers based on chunk offset
                chunk_id = result.get("chunk_id", "")
                if chunk_id:
                    # Find chunk metadata to adjust line numbers
                    chunk_info = next(
                        (c for c in original_metadata.get("chunks", []) 
                         if c["id"] == chunk_id), 
                        None
                    )
                    
                    if chunk_info:
                        offset = chunk_info["start_line"]
                        for vuln in chunk_vulns:
                            if vuln.get("line_number"):
                                vuln["line_number"] += offset
                
                merged_vulnerabilities.extend(chunk_vulns)
            
            # Merge metrics
            if "metrics" in result:
                for key, value in result["metrics"].items():
                    if key in merged_metrics:
                        if isinstance(value, (int, float)):
                            merged_metrics[key] += value
                        elif isinstance(value, list):
                            merged_metrics[key].extend(value)
                    else:
                        merged_metrics[key] = value
            
            # Sum execution metrics
            total_execution_time += result.get("execution_time", 0)
            total_tokens_used += result.get("tokens_used", 0)
        
        # Remove duplicate vulnerabilities
        unique_vulnerabilities = self._deduplicate_vulnerabilities(merged_vulnerabilities)
        
        return {
            "vulnerabilities": unique_vulnerabilities,
            "metrics": merged_metrics,
            "execution_time": total_execution_time,
            "tokens_used": total_tokens_used,
            "analysis_method": "chunked",
            "chunks_analyzed": len(chunk_results)
        }
    
    def _deduplicate_vulnerabilities(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate vulnerabilities from merged results"""
        
        seen = set()
        unique_vulns = []
        
        for vuln in vulnerabilities:
            # Create a key based on location and type
            key = (
                vuln.get("line_number"),
                vuln.get("function_name"),
                vuln.get("category"),
                vuln.get("title")
            )
            
            if key not in seen:
                seen.add(key)
                unique_vulns.append(vuln)
        
        return unique_vulns
