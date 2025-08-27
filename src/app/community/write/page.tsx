'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Upload, Tag, Eye } from 'lucide-react'

export default function WritePage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isPreview, setIsPreview] = useState(false)
  
  const [formData, setFormData] = useState({
    category: '',
    title: '',
    content: '',
    tags: '',
    files: [] as File[]
  })

  const categories = [
    { key: 'strategy', label: '전략토론방' },
    { key: 'free', label: '자유게시판' },
    { key: 'market', label: '마켓브리핑' },
    { key: 'notice', label: '공지사항' }
  ]

  // URL 파라미터에서 카테고리 설정
  useEffect(() => {
    const category = searchParams.get('category')
    if (category) {
      setFormData(prev => ({ ...prev, category }))
    }
  }, [searchParams])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setFormData(prev => ({ ...prev, files: [...prev.files, ...files] }))
  }

  const removeFile = (index: number) => {
    setFormData(prev => ({
      ...prev,
      files: prev.files.filter((_, i) => i !== index)
    }))
  }

  const handleSave = (isDraft = false) => {
    // 실제로는 API 호출
    console.log('Saving post:', { ...formData, isDraft })
    alert(isDraft ? '임시저장 되었습니다.' : '게시글이 등록되었습니다.')
    if (!isDraft) {
      router.push('/community')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <Link href="/community">
              <button className="p-2 text-gray-400 hover:text-white transition-colors">
                <ArrowLeft className="w-6 h-6" />
              </button>
            </Link>
            <h1 className="text-3xl font-bold text-white">글쓰기</h1>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsPreview(!isPreview)}
              className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                isPreview ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <Eye className="w-4 h-4" />
              <span>미리보기</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-3">
            {!isPreview ? (
              <div className="space-y-6">
                {/* Category Selection */}
                <div>
                  <label className="block text-white font-medium mb-2">카테고리 선택</label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleInputChange}
                    className="w-full bg-gray-800 text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-green-500"
                    required
                  >
                    <option value="">카테고리를 선택하세요</option>
                    {categories.map(cat => (
                      <option key={cat.key} value={cat.key}>{cat.label}</option>
                    ))}
                  </select>
                </div>

                {/* Title Input */}
                <div>
                  <label className="block text-white font-medium mb-2">제목</label>
                  <input
                    type="text"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder="제목을 입력하세요"
                    className="w-full bg-gray-800 text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-green-500"
                    maxLength={100}
                    required
                  />
                  <div className="text-right text-gray-400 text-sm mt-1">
                    {formData.title.length}/100
                  </div>
                </div>

                {/* Content Input */}
                <div>
                  <label className="block text-white font-medium mb-2">내용</label>
                  <textarea
                    name="content"
                    value={formData.content}
                    onChange={handleInputChange}
                    placeholder="내용을 입력하세요"
                    className="w-full bg-gray-800 text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:border-green-500 resize-vertical"
                    rows={15}
                    maxLength={5000}
                    required
                  />
                  <div className="text-right text-gray-400 text-sm mt-1">
                    {formData.content.length}/5000
                  </div>
                </div>

                {/* File Upload */}
                <div>
                  <label className="block text-white font-medium mb-2">파일 첨부</label>
                  <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center hover:border-gray-500 transition-colors">
                    <input
                      type="file"
                      id="file-upload"
                      multiple
                      onChange={handleFileUpload}
                      className="hidden"
                      accept=".jpg,.jpeg,.png,.gif,.pdf,.doc,.docx,.txt"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-gray-400">파일을 선택하거나 드래그해서 업로드하세요</p>
                      <p className="text-gray-500 text-sm mt-1">
                        최대 10MB, 이미지/문서 파일만 지원
                      </p>
                    </label>
                  </div>
                  
                  {/* Uploaded Files */}
                  {formData.files.length > 0 && (
                    <div className="mt-4 space-y-2">
                      {formData.files.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-800 px-4 py-2 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <span className="text-white">{file.name}</span>
                            <span className="text-gray-400 text-sm">({formatFileSize(file.size)})</span>
                          </div>
                          <button
                            onClick={() => removeFile(index)}
                            className="text-red-400 hover:text-red-300"
                          >
                            삭제
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Tags Input */}
                <div>
                  <label className="block text-white font-medium mb-2">태그</label>
                  <div className="relative">
                    <Tag className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      name="tags"
                      value={formData.tags}
                      onChange={handleInputChange}
                      placeholder="태그를 쉼표로 구분해서 입력하세요 (예: 퀀트, 투자전략, 백테스팅)"
                      className="w-full bg-gray-800 text-white border border-gray-600 rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:border-green-500"
                    />
                  </div>
                  <p className="text-gray-400 text-sm mt-1">
                    관련 키워드를 입력하면 다른 사용자가 쉽게 찾을 수 있습니다
                  </p>
                </div>
              </div>
            ) : (
              /* Preview Mode */
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="border-b border-gray-600 pb-4 mb-6">
                  <div className="text-green-400 text-sm mb-2">
                    {categories.find(c => c.key === formData.category)?.label || '카테고리 미선택'}
                  </div>
                  <h1 className="text-2xl font-bold text-white mb-4">
                    {formData.title || '제목을 입력하세요'}
                  </h1>
                  <div className="text-gray-400 text-sm">
                    작성자 | {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()} | 조회수 0
                  </div>
                </div>
                <div className="text-white whitespace-pre-wrap leading-relaxed">
                  {formData.content || '내용을 입력하세요'}
                </div>
                {formData.tags && (
                  <div className="mt-6 pt-4 border-t border-gray-600">
                    <div className="flex flex-wrap gap-2">
                      {formData.tags.split(',').map((tag, index) => (
                        <span key={index} className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
                          #{tag.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-gray-800 rounded-lg p-6 sticky top-8">
              <h3 className="text-white font-semibold mb-4">작성 가이드</h3>
              <div className="space-y-4 text-sm text-gray-300">
                <div>
                  <h4 className="text-white font-medium mb-2">글쓰기 규칙</h4>
                  <ul className="space-y-1 text-gray-400">
                    <li>• 명확하고 구체적인 제목 작성</li>
                    <li>• 정중하고 건설적인 내용</li>
                    <li>• 스팸성 내용 금지</li>
                    <li>• 저작권 침해 금지</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-white font-medium mb-2">추천 태그</h4>
                  <div className="flex flex-wrap gap-1">
                    {['퀀트', '백테스팅', '투자전략', '알고리즘'].map(tag => (
                      <button
                        key={tag}
                        onClick={() => {
                          const currentTags = formData.tags ? formData.tags + ', ' : ''
                          setFormData(prev => ({ ...prev, tags: currentTags + tag }))
                        }}
                        className="bg-gray-700 hover:bg-gray-600 text-gray-300 px-2 py-1 rounded text-xs transition-colors"
                      >
                        #{tag}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between mt-8">
          <button
            onClick={() => handleSave(true)}
            className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg transition-colors"
          >
            임시저장
          </button>
          <div className="flex space-x-4">
            <Link href="/community">
              <button className="bg-gray-600 hover:bg-gray-500 text-white px-6 py-3 rounded-lg transition-colors">
                취소
              </button>
            </Link>
            <button
              onClick={() => handleSave(false)}
              className="bg-green-600 hover:bg-green-500 text-white px-6 py-3 rounded-lg transition-colors"
              disabled={!formData.category || !formData.title || !formData.content}
            >
              등록
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}