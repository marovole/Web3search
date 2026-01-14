declare module 'react-syntax-highlighter/dist/esm/prism-light' {
  import Prism from 'react-syntax-highlighter/dist/esm/prism-light'
  export = Prism
}

declare module 'react-syntax-highlighter/dist/esm/styles/prism' {
  const styles: Record<string, object>
  export = styles
}

declare module 'react-syntax-highlighter/dist/esm/languages/prism/*' {
  const lang: object
  export = lang
}
