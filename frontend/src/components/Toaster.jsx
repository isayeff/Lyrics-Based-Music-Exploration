import { Toaster as HotToaster } from 'react-hot-toast'

/* Toast notifications, styled to the app's dark palette rather than the
   library's light default. Mounted once in App. */
export default function Toaster() {
  return (
    <HotToaster
      position="top-center"
      toastOptions={{
        duration: 3000,
        style: {
          background: '#141416',
          color: '#F5F5F5',
          border: '1px solid #26262A',
          borderRadius: '10px',
          fontSize: '13px',
          padding: '10px 14px',
          boxShadow: '0 10px 30px -10px rgba(0,0,0,0.8)',
        },
        success: {
          iconTheme: { primary: '#30A46C', secondary: '#141416' },
        },
        error: {
          duration: 4500,
          iconTheme: { primary: '#E80003', secondary: '#141416' },
        },
      }}
    />
  )
}
