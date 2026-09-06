import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import CalendarPage from './pages/CalendarPage'
import './App.css'

export default function App() {
  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#c47878',
          borderRadius: 10,
          fontFamily:
            '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
        },
      }}
    >
      <CalendarPage />
    </ConfigProvider>
  )
}
