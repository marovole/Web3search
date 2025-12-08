import React from 'react'
import { FileText } from 'lucide-react'

const ReportsPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
        <FileText className="w-8 h-8 text-primary" />
      </div>
      <h1 className="text-2xl font-display font-bold text-foreground mb-3">报告功能</h1>
      <p className="text-muted-foreground max-w-md">此功能正在开发中，敬请期待...</p>
    </div>
  )
}

export default ReportsPage
