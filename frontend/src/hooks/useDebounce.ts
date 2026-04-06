import { useEffect, useState } from "react"

// funcao usada para a query só ocorrer num delay em ms, assim não tem tanta query no banco
// a cada digitacao do user
export function useDebounce<T>(value: T, delay = 400) {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debounced
}