import { useState, type MouseEvent as ReactMouseEvent } from 'react';
import AppBar from '@mui/material/AppBar';
import Avatar from '@mui/material/Avatar';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import IconButton from '@mui/material/IconButton';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import AccountCircleOutlinedIcon from '@mui/icons-material/AccountCircleOutlined';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth';

const Header = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [menuAnchorElement, setMenuAnchorElement] = useState<HTMLElement | null>(null);
  const isUserMenuOpen = Boolean(menuAnchorElement);

  const handleOpenUserMenu = (event: ReactMouseEvent<HTMLElement>) => {
    setMenuAnchorElement(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setMenuAnchorElement(null);
  };

  const handleLogout = async () => {
    handleCloseUserMenu();
    await logout();
    navigate('/login');
  };

  return (
    <AppBar
      position="sticky"
      elevation={1}
      sx={{
        backgroundColor: 'rgba(255, 255, 255, 0.92)',
        backdropFilter: 'blur(6px)',
        color: 'text.primary',
      }}
    >
      <Toolbar sx={{ px: { xs: 2, sm: 3 } }}>
        <Typography
          component={RouterLink}
          to={isAuthenticated ? '/dashboard' : '/'}
          variant="h6"
          sx={{
            textDecoration: 'none',
            fontWeight: 700,
            flexGrow: 1,
          }}
          className="text-primary-900"
        >
          Application Hub
        </Typography>

        {isAuthenticated ? (
          <>
            <IconButton
              aria-label="Open user menu"
              aria-controls={isUserMenuOpen ? 'header-user-menu' : undefined}
              aria-expanded={isUserMenuOpen ? 'true' : undefined}
              aria-haspopup="true"
              onClick={handleOpenUserMenu}
            >
              <Avatar sx={{ width: 34, height: 34, backgroundColor: 'white' }}>
                <AccountCircleOutlinedIcon
                  fontSize="medium"
                  sx={{ color: 'rgb(12 61 102)', backgroundColor: 'white' }}
                />
              </Avatar>
            </IconButton>

            <Menu
              id="header-user-menu"
              anchorEl={menuAnchorElement}
              open={isUserMenuOpen}
              onClose={handleCloseUserMenu}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              keepMounted
            >
              <MenuItem component="a" href="#profile" onClick={handleCloseUserMenu}>
                Profile
              </MenuItem>
              <MenuItem onClick={() => void handleLogout()} disabled={isLoading}>
                {isLoading ? (
                  <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    Logging out...
                  </Box>
                ) : (
                  'Logout'
                )}
              </MenuItem>
            </Menu>
          </>
        ) : (
          <Button
            component={RouterLink}
            to="/login"
            sx={{ color: 'rgb(12 61 102);', fontWeight: 600 }}
            variant="text"
          >
            Login
          </Button>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;
