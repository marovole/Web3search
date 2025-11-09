#!/bin/bash

# ============================================
# Render PostgreSQL 数据库导出脚本
# ============================================
#
# 使用说明:
# 1. 从 Render Dashboard 获取数据库连接信息
# 2. 设置环境变量（见下方）
# 3. 运行: chmod +x export_render_data.sh && ./export_render_data.sh
#
# ============================================

set -e  # 遇到错误立即退出

# ============================================
# 配置区域 - 请填写你的 Render 数据库信息
# ============================================

# 方式 1: 直接设置（不推荐，不要提交到 git）
# RENDER_HOST="dpg-xxxxx.render.com"
# RENDER_USER="web3search_user"
# RENDER_DATABASE="web3search"
# RENDER_PASSWORD="your-password"

# 方式 2: 使用环境变量（推荐）
# 在终端中运行:
# export RENDER_HOST="dpg-xxxxx.render.com"
# export RENDER_USER="web3search_user"
# export RENDER_DATABASE="web3search"
# export RENDER_PASSWORD="your-password"

# 或者使用 .env 文件
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# ============================================
# 检查必需的环境变量
# ============================================

if [ -z "$RENDER_HOST" ] || [ -z "$RENDER_USER" ] || [ -z "$RENDER_DATABASE" ]; then
  echo "❌ 错误: 缺少必需的环境变量"
  echo ""
  echo "请设置以下环境变量:"
  echo "  export RENDER_HOST='dpg-xxxxx.render.com'"
  echo "  export RENDER_USER='web3search_user'"
  echo "  export RENDER_DATABASE='web3search'"
  echo "  export RENDER_PASSWORD='your-password'"
  echo ""
  echo "或创建 .env 文件:"
  echo "  RENDER_HOST=dpg-xxxxx.render.com"
  echo "  RENDER_USER=web3search_user"
  echo "  RENDER_DATABASE=web3search"
  echo "  RENDER_PASSWORD=your-password"
  exit 1
fi

# ============================================
# 配置
# ============================================

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SCHEMA_FILE="${BACKUP_DIR}/render_schema_${TIMESTAMP}.sql"
DATA_FILE="${BACKUP_DIR}/render_data_${TIMESTAMP}.sql"
FULL_BACKUP="${BACKUP_DIR}/render_full_${TIMESTAMP}.sql"
ARCHIVE_FILE="${BACKUP_DIR}/render_backup_${TIMESTAMP}.tar.gz"

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

echo "================================================"
echo "🚀 开始导出 Render PostgreSQL 数据库"
echo "================================================"
echo ""
echo "数据库信息:"
echo "  Host: ${RENDER_HOST}"
echo "  User: ${RENDER_USER}"
echo "  Database: ${RENDER_DATABASE}"
echo "  Backup Directory: ${BACKUP_DIR}"
echo ""

# ============================================
# Step 1: 导出 Schema（表结构）
# ============================================

echo "📦 Step 1/4: 导出数据库 Schema..."
export PGPASSWORD="${RENDER_PASSWORD}"

pg_dump \
  -h "${RENDER_HOST}" \
  -U "${RENDER_USER}" \
  -d "${RENDER_DATABASE}" \
  --schema-only \
  --no-owner \
  --no-privileges \
  --file="${SCHEMA_FILE}"

if [ -f "${SCHEMA_FILE}" ]; then
  echo "✅ Schema 导出成功: ${SCHEMA_FILE}"
  echo "   文件大小: $(du -h "${SCHEMA_FILE}" | cut -f1)"
else
  echo "❌ Schema 导出失败"
  exit 1
fi

echo ""

# ============================================
# Step 2: 导出数据
# ============================================

echo "📊 Step 2/4: 导出数据库数据..."

pg_dump \
  -h "${RENDER_HOST}" \
  -U "${RENDER_USER}" \
  -d "${RENDER_DATABASE}" \
  --data-only \
  --no-owner \
  --no-privileges \
  --file="${DATA_FILE}"

if [ -f "${DATA_FILE}" ]; then
  echo "✅ 数据导出成功: ${DATA_FILE}"
  echo "   文件大小: $(du -h "${DATA_FILE}" | cut -f1)"
else
  echo "❌ 数据导出失败"
  exit 1
fi

echo ""

# ============================================
# Step 3: 完整备份（Schema + Data）
# ============================================

echo "💾 Step 3/4: 创建完整备份..."

pg_dump \
  -h "${RENDER_HOST}" \
  -U "${RENDER_USER}" \
  -d "${RENDER_DATABASE}" \
  --no-owner \
  --no-privileges \
  --file="${FULL_BACKUP}"

if [ -f "${FULL_BACKUP}" ]; then
  echo "✅ 完整备份成功: ${FULL_BACKUP}"
  echo "   文件大小: $(du -h "${FULL_BACKUP}" | cut -f1)"
else
  echo "❌ 完整备份失败"
  exit 1
fi

echo ""

# ============================================
# Step 4: 压缩备份文件
# ============================================

echo "🗜️  Step 4/4: 压缩备份文件..."

tar -czf "${ARCHIVE_FILE}" \
  "${SCHEMA_FILE}" \
  "${DATA_FILE}" \
  "${FULL_BACKUP}"

if [ -f "${ARCHIVE_FILE}" ]; then
  echo "✅ 备份压缩成功: ${ARCHIVE_FILE}"
  echo "   压缩包大小: $(du -h "${ARCHIVE_FILE}" | cut -f1)"
else
  echo "❌ 备份压缩失败"
  exit 1
fi

echo ""

# ============================================
# Step 5: 验证备份
# ============================================

echo "🔍 验证备份文件..."

# 检查 schema 文件是否包含表定义
if grep -q "CREATE TABLE" "${SCHEMA_FILE}"; then
  echo "✅ Schema 文件包含表定义"
else
  echo "⚠️  警告: Schema 文件可能不完整"
fi

# 检查数据文件是否包含 COPY 语句
if grep -q "COPY" "${DATA_FILE}"; then
  echo "✅ 数据文件包含数据记录"
else
  echo "⚠️  警告: 数据文件可能为空"
fi

echo ""

# ============================================
# 完成
# ============================================

echo "================================================"
echo "✅ 数据库导出完成！"
echo "================================================"
echo ""
echo "导出文件:"
echo "  1. Schema:       ${SCHEMA_FILE}"
echo "  2. Data:         ${DATA_FILE}"
echo "  3. Full Backup:  ${FULL_BACKUP}"
echo "  4. Archive:      ${ARCHIVE_FILE}"
echo ""
echo "下一步:"
echo "  1. 验证导出文件的内容"
echo "  2. 上传到云存储（S3/GCS）保存"
echo "  3. 在 Supabase 中执行 schema 迁移"
echo "  4. 导入数据到 Supabase"
echo ""
echo "清理（可选）:"
echo "  # 保留压缩包，删除原始文件"
echo "  rm ${SCHEMA_FILE} ${DATA_FILE} ${FULL_BACKUP}"
echo ""
echo "================================================"

# 清理密码环境变量
unset PGPASSWORD
