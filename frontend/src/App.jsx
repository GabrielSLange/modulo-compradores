import { useState, useEffect } from 'react'

function App() {
  const [apiData, setApiData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Fazendo a chamada para o nosso Controller no backend
    fetch('http://127.0.0.1:8080/api/ping')
      .then(response => {
        if (!response.ok) throw new Error('Erro na rede')
        return response.json()
      })
      .then(data => setApiData(data))
      .catch(err => setError(err.message))
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Teste de Integração do Módulo</h1>

      {error && <p style={{ color: 'red' }}>Erro ao conectar: {error}</p>}

      {apiData ? (
        <div style={{ background: '#f4f4f4', padding: '1rem', borderRadius: '8px' }}>
          <p style={{ color: 'black' }}><strong>Status:</strong> {apiData.status}</p>
          <p style={{ color: 'black' }}><strong>Mensagem:</strong> {apiData.message}</p>
          <p style={{ color: 'black' }}><strong>Módulo:</strong> {apiData.module}</p>
        </div>
      ) : (
        !error && <p>Carregando dados da API...</p>
      )}
    </div>
  )
}

export default App