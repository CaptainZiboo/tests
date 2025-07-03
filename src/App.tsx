import { useState } from 'react'
import { Amplify } from 'aws-amplify'
// @ts-ignore
import awsExports from './aws-exports'

Amplify.configure(awsExports)

const API_BASE_URL = 'https://tkc4uoslof.execute-api.eu-west-1.amazonaws.com/dev'

interface User {
  id: string
  email: string
  name?: string
}

interface CreateUserData {
  email: string
  name: string
}

function App() {
  // État pour la création d'utilisateur
  const [createForm, setCreateForm] = useState<CreateUserData>({ email: '', name: '' })
  const [createLoading, setCreateLoading] = useState(false)
  const [createMessage, setCreateMessage] = useState('')

  // État pour la recherche d'utilisateur
  const [searchEmail, setSearchEmail] = useState('')
  const [searchResult, setSearchResult] = useState<User | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchMessage, setSearchMessage] = useState('')

  // Fonction pour créer un utilisateur
  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!createForm.email || !createForm.name) {
      setCreateMessage('Veuillez remplir tous les champs')
      return
    }

    setCreateLoading(true)
    setCreateMessage('')

    try {
      const response = await fetch(`${API_BASE_URL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: createForm.email,
          name: createForm.name
        })
      })

      const data = await response.json()

      if (response.ok) {
        setCreateMessage(`Utilisateur créé avec succès! ID: ${data.id}`)
        setCreateForm({ email: '', name: '' })
      } else {
        setCreateMessage(`Erreur: ${data.error}`)
      }
    } catch (error) {
      setCreateMessage('Erreur de connexion au serveur')
      console.error('Erreur lors de la création:', error)
    } finally {
      setCreateLoading(false)
    }
  }

  // Fonction pour rechercher un utilisateur
  const handleSearchUser = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!searchEmail) {
      setSearchMessage('Veuillez saisir un email')
      return
    }

    setSearchLoading(true)
    setSearchMessage('')
    setSearchResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/users?email=${encodeURIComponent(searchEmail)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      const data = await response.json()

      if (response.ok) {
        setSearchResult(data)
        setSearchMessage('Utilisateur trouvé!')
      } else {
        setSearchMessage(`Erreur: ${data.error}`)
      }
    } catch (error) {
      setSearchMessage('Erreur de connexion au serveur')
      console.error('Erreur lors de la recherche:', error)
    } finally {
      setSearchLoading(false)
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Gestion des Utilisateurs</h1>
      </header>

      <div className="app-content">
        {/* Section Création d'utilisateur */}
        <div className="section create-section">
          <h2>Créer un Utilisateur</h2>
          <form onSubmit={handleCreateUser} className="user-form">
            <div className="form-group">
              <label htmlFor="create-email">Email:</label>
              <input
                type="email"
                id="create-email"
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                placeholder="exemple@email.com"
                required
                disabled={createLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="create-name">Nom complet:</label>
              <input
                type="text"
                id="create-name"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                placeholder="Prénom Nom"
                required
                disabled={createLoading}
              />
            </div>

            <button
              type="submit"
              className="submit-button"
              disabled={createLoading}
            >
              {createLoading ? 'Création...' : 'Créer l\'utilisateur'}
            </button>
          </form>

          {createMessage && (
            <div className={`message ${createMessage.includes('Erreur') ? 'error' : 'success'}`}>
              {createMessage}
            </div>
          )}
        </div>

        {/* Section Recherche d'utilisateur */}
        <div className="section search-section">
          <h2>Rechercher un Utilisateur</h2>
          <form onSubmit={handleSearchUser} className="user-form">
            <div className="form-group">
              <label htmlFor="search-email">Email à rechercher:</label>
              <input
                type="email"
                id="search-email"
                value={searchEmail}
                onChange={(e) => setSearchEmail(e.target.value)}
                placeholder="exemple@email.com"
                required
                disabled={searchLoading}
              />
            </div>

            <button
              type="submit"
              className="submit-button"
              disabled={searchLoading}
            >
              {searchLoading ? 'Recherche...' : 'Rechercher'}
            </button>
          </form>

          {searchMessage && (
            <div className={`message ${searchMessage.includes('Erreur') ? 'error' : 'success'}`}>
              {searchMessage}
            </div>
          )}

          {searchResult && (
            <div className="user-result">
              <h3>Utilisateur trouvé:</h3>
              <div className="user-details">
                <p><strong>ID:</strong> {searchResult.id}</p>
                <p><strong>Email:</strong> {searchResult.email}</p>
                {searchResult.name && <p><strong>Nom:</strong> {searchResult.name}</p>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App