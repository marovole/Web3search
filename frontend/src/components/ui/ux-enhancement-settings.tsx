import React from 'react'

export const UXEnhancementSettings: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="rounded-lg border p-6 bg-card">
        <h2 className="text-xl font-semibold mb-2">UX 增强设置</h2>
        <p className="text-sm text-muted-foreground">
          该版本已临时禁用高级 UX 增强控制面板，以保证发布稳定性。
          核心功能不受影响，后续可在不影响构建的前提下恢复完整面板。
        </p>
      </div>
    </div>
  )
}
