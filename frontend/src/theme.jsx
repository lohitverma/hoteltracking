import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#9c27b0',
      light: '#ba68c8',
      dark: '#7b1fa2',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    success: {
      main: '#4caf50',
      light: '#81c784',
      dark: '#388e3c',
    },
    error: {
      main: '#f44336',
      light: '#e57373',
      dark: '#d32f2f',
    },
    warning: {
      main: '#ff9800',
      light: '#ffb74d',
      dark: '#f57c00',
    },
    info: {
      main: '#2196f3',
      light: '#64b5f6',
      dark: '#1976d2',
    },
    text: {
      primary: '#1a2027',
      secondary: '#637381',
    },
    divider: 'rgba(145, 158, 171, 0.24)',
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 8,
  },
  shadows: [
    'none',
    '0px 2px 4px rgba(145, 158, 171, 0.16)',
    '0px 4px 8px rgba(145, 158, 171, 0.16)',
    '0px 8px 16px rgba(145, 158, 171, 0.16)',
    '0px 12px 24px rgba(145, 158, 171, 0.16)',
    '0px 16px 32px rgba(145, 158, 171, 0.16)',
    '0px 20px 40px rgba(145, 158, 171, 0.16)',
    '0px 24px 48px rgba(145, 158, 171, 0.16)',
    '0px 28px 56px rgba(145, 158, 171, 0.16)',
    '0px 32px 64px rgba(145, 158, 171, 0.16)',
    '0px 36px 72px rgba(145, 158, 171, 0.16)',
    '0px 40px 80px rgba(145, 158, 171, 0.16)',
    '0px 44px 88px rgba(145, 158, 171, 0.16)',
    '0px 48px 96px rgba(145, 158, 171, 0.16)',
    '0px 52px 104px rgba(145, 158, 171, 0.16)',
    '0px 56px 112px rgba(145, 158, 171, 0.16)',
    '0px 60px 120px rgba(145, 158, 171, 0.16)',
    '0px 64px 128px rgba(145, 158, 171, 0.16)',
    '0px 68px 136px rgba(145, 158, 171, 0.16)',
    '0px 72px 144px rgba(145, 158, 171, 0.16)',
    '0px 76px 152px rgba(145, 158, 171, 0.16)',
    '0px 80px 160px rgba(145, 158, 171, 0.16)',
    '0px 84px 168px rgba(145, 158, 171, 0.16)',
    '0px 88px 176px rgba(145, 158, 171, 0.16)',
    '0px 92px 184px rgba(145, 158, 171, 0.16)',
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          padding: '8px 16px',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
        contained: {
          boxShadow: '0px 2px 4px rgba(145, 158, 171, 0.16)',
          '&:hover': {
            boxShadow: '0px 8px 16px rgba(145, 158, 171, 0.16)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0px 4px 8px rgba(145, 158, 171, 0.16)',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: '0px 8px 16px rgba(145, 158, 171, 0.16)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            transition: 'all 0.2s ease-in-out',
            '&:hover': {
              boxShadow: '0px 4px 8px rgba(145, 158, 171, 0.16)',
            },
            '&.Mui-focused': {
              boxShadow: '0px 4px 8px rgba(145, 158, 171, 0.16)',
            },
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          padding: '16px',
        },
        head: {
          fontWeight: 600,
          backgroundColor: '#f8fafc',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid rgba(145, 158, 171, 0.24)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0px 2px 4px rgba(145, 158, 171, 0.16)',
        },
      },
    },
  },
});

export default theme;
