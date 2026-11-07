import { FileText, Globe, GraduationCap } from 'lucide-react'

// 3 nguồn tri thức theo thiết kế hệ thống: tài liệu người dùng, web, cơ sở dữ liệu học thuật
export const SOURCE_TYPES = {
  document: { label: 'My document', Icon: FileText, badge: 'bg-sky-100 text-sky-700' },
  web: { label: 'Web', Icon: Globe, badge: 'bg-emerald-100 text-emerald-700' },
  academic: { label: 'Academic', Icon: GraduationCap, badge: 'bg-violet-100 text-violet-700' },
}

export const getSourceType = (type) => SOURCE_TYPES[type] ?? SOURCE_TYPES.web
