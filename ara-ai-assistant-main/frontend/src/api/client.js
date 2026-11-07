import axios from 'axios'

/** true -> dùng dữ liệu giả trong api/mock.js (đặt trong file .env) */
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '', // rỗng = đi qua proxy của Vite
  timeout: 120_000, // LLM trả lời có thể chậm
})

// Chuẩn hoá lỗi: luôn ném ra Error có message đọc được
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : error.code === 'ECONNABORTED'
          ? 'The request timed out. Please try again.'
          : error.response
            ? `Server error (${error.response.status})`
            : 'Cannot reach the server. Is the backend running?'
    return Promise.reject(new Error(message))
  },
)
