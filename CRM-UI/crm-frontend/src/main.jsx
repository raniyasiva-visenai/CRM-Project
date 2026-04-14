import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const theme = createTheme({
    palette: {
        primary: {
            main: '#0f172a', // Midnight Blue
            light: '#1e293b',
            dark: '#020617',
        },
        secondary: {
            main: '#c5a059', // Classic Gold
        },
        background: {
            default: '#fcfcfc',
            paper: '#ffffff',
        },
        text: {
            primary: '#0f172a',
            secondary: '#64748b',
        },
    },
    typography: {
        fontFamily: '"Outfit", "Inter", "system-ui", sans-serif',
        h4: {
            fontWeight: 800,
            letterSpacing: '-0.02em',
        },
        subtitle1: {
            fontWeight: 600,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
        },
    },
    shape: {
        borderRadius: 12,
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: 'none',
                    fontWeight: 600,
                    padding: '8px 20px',
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    boxShadow: '0 4px 20px -5px rgba(0, 0, 0, 0.05)',
                    border: '1px solid rgba(0,0,0,0.04)',
                },
            },
        },
    },
});

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <App />
        </ThemeProvider>
    </React.StrictMode>,
)
