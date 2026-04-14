import React, { useState } from 'react';
import {
    Box, Paper, Typography, TextField, Button,
    Container, InputAdornment, IconButton, Chip
} from '@mui/material';
import LockOutlined from '@mui/icons-material/LockOutlined';
import EmailOutlined from '@mui/icons-material/EmailOutlined';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

export default function Login({ onLogin }) {
    const [email, setEmail] = useState("admin@maruthamprop.com");
    const [pwd, setPwd] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        onLogin(email, pwd);
    };

    return (
        <Box sx={{
            flex: 1,
            width: '100%',
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'primary.main',
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Background Accents */}
            <Box sx={{
                position: 'absolute', top: -100, left: -100, width: 400, height: 400,
                bgcolor: 'secondary.main', opacity: 0.05, borderRadius: '50%', filter: 'blur(80px)'
            }} />
            <Box sx={{
                position: 'absolute', bottom: -50, right: -50, width: 300, height: 300,
                bgcolor: 'white', opacity: 0.05, borderRadius: '50%', filter: 'blur(60px)'
            }} />

            <Container maxWidth="xs">
                <Paper sx={{
                    p: 6,
                    borderRadius: 4,
                    boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
                    textAlign: 'center',
                    border: '1px solid rgba(255,255,255,0.05)',
                    bgcolor: 'background.paper'
                }}>
                    <Box sx={{
                        display: 'inline-flex',
                        p: 1.5,
                        bgcolor: 'primary.main',
                        borderRadius: 2,
                        mb: 4,
                        boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)'
                    }}>
                        <Typography variant="h5" sx={{ fontWeight: 900, color: 'secondary.main' }}>I</Typography>
                    </Box>

                    <Typography variant="h5" color="primary" sx={{ fontWeight: 800, mb: 0.5 }}>
                        IRIS Engine
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase', display: 'block', mb: 4 }}>
                        Secured Management Portal
                    </Typography>

                    <form onSubmit={handleSubmit}>
                        <TextField
                            fullWidth
                            label="Institutional Email"
                            variant="outlined"
                            value={email}
                            onChange={e => setEmail(e.target.value)}
                            margin="normal"
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <EmailOutlined fontSize="small" color="action" />
                                    </InputAdornment>
                                ),
                            }}
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            fullWidth
                            label="Access Password"
                            type={showPassword ? 'text' : 'password'}
                            variant="outlined"
                            value={pwd}
                            onChange={e => setPwd(e.target.value)}
                            margin="normal"
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <LockOutlined fontSize="small" color="action" />
                                    </InputAdornment>
                                ),
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                                            {showPassword ? <VisibilityOff fontSize="small" /> : <Visibility fontSize="small" />}
                                        </IconButton>
                                    </InputAdornment>
                                )
                            }}
                            sx={{ mb: 4 }}
                        />
                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            color="primary"
                            size="large"
                            sx={{
                                py: 1.8,
                                fontWeight: 800,
                                fontSize: 13,
                                letterSpacing: 1,
                                bgcolor: 'primary.main',
                                '&:hover': { bgcolor: 'primary.light' }
                            }}
                        >
                            AUTHENTICATE SESSION
                        </Button>
                    </form>

                    <Box sx={{ mt: 6, pt: 3, borderTop: '1px solid rgba(0,0,0,0.05)' }}>
                        <Typography variant="caption" sx={{ color: 'text.disabled', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                            Environment: <Box component="span" sx={{ color: 'success.main' }}>PRODUCTION</Box>
                        </Typography>
                    </Box>
                </Paper>
            </Container>
        </Box>
    );
}
