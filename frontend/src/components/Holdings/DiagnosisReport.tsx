import React from 'react'
import type { PortfolioDiagnosis } from '../../hooks/useDiagnosis'

interface DiagnosisReportProps {
  diagnosis: PortfolioDiagnosis
}

const ScoreGauge: React.FC<{ score: number; label: string; color: string }> = ({ score, label, color }) => {
  const getScoreColor = (s: number) => {
    if (s >= 80) return 'text-green-600'
    if (s >= 60) return 'text-blue-600'
    if (s >= 40) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="text-center">
      <div className={`text-3xl font-bold ${getScoreColor(score)}`}>{score}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
      <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  )
}

const DiagnosisReport: React.FC<DiagnosisReportProps> = ({ diagnosis }) => {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold">投资组合健康评分</h3>
            <p className="text-indigo-200 text-sm">{formatDate(diagnosis.diagnosis_date)}</p>
          </div>
          <div className="text-5xl font-bold">{diagnosis.overall_health_score}</div>
        </div>
        <p className="text-indigo-100">{diagnosis.summary}</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <ScoreGauge 
            score={diagnosis.diversification_score} 
            label="多样化" 
            color="bg-blue-500"
          />
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <ScoreGauge 
            score={diagnosis.risk_score} 
            label="风险控制" 
            color="bg-green-500"
          />
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
          <ScoreGauge 
            score={diagnosis.performance_score} 
            label="表现" 
            color="bg-purple-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {diagnosis.strengths.length > 0 && (
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              优势
            </h4>
            <ul className="space-y-2">
              {diagnosis.strengths.map((strength, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <svg className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  {strength}
                </li>
              ))}
            </ul>
          </div>
        )}

        {diagnosis.weaknesses.length > 0 && (
          <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
              需改进
            </h4>
            <ul className="space-y-2">
              {diagnosis.weaknesses.map((weakness, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <svg className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {weakness}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {diagnosis.recommendations.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            投资建议
          </h4>
          <ul className="space-y-3">
            {diagnosis.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg text-sm text-gray-700">
                <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                  {i + 1}
                </span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}

      {diagnosis.risk_factors.length > 0 && (
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            风险因素
          </h4>
          <div className="space-y-3">
            {diagnosis.risk_factors.map((risk, i) => (
              <div 
                key={i} 
                className={`p-3 rounded-lg border ${getSeverityColor(risk.severity)}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{risk.factor.replace(/_/g, ' ')}</span>
                  <span className="text-xs uppercase font-semibold">{risk.severity}</span>
                </div>
                <p className="text-sm opacity-80">{risk.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {diagnosis.full_report && (
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-200">
          <h4 className="font-semibold text-gray-900 mb-3">详细报告</h4>
          <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
            {diagnosis.full_report}
          </div>
        </div>
      )}
    </div>
  )
}

export default DiagnosisReport
