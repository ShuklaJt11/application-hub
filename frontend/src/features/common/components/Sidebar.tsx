import { useEffect, useState } from 'react';
import type { CSSObject, Theme } from '@mui/material/styles';
import { styled, useTheme } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import NotificationsNoneOutlinedIcon from '@mui/icons-material/NotificationsNoneOutlined';
import MenuOutlinedIcon from '@mui/icons-material/MenuOutlined';
import WorkOutlineOutlinedIcon from '@mui/icons-material/WorkOutlineOutlined';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '@/features/auth';

const drawerWidth = 240;

const openedMixin = (theme: Theme): CSSObject => ({
  width: drawerWidth,
  overflowX: 'hidden',
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
});

const closedMixin = (theme: Theme): CSSObject => ({
  overflowX: 'hidden',
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  width: `calc(${theme.spacing(7)} + 1px)`,
  [theme.breakpoints.up('sm')]: {
    width: `calc(${theme.spacing(8)} + 1px)`,
  },
});

const DrawerHeader = styled('div')(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'flex-end',
  padding: theme.spacing(1),
  minHeight: theme.spacing(8),
}));

const MiniDrawer = styled(Drawer, { shouldForwardProp: (prop) => prop !== 'open' })<{
  open: boolean;
}>(({ theme, open }) => ({
  width: drawerWidth,
  flexShrink: 0,
  whiteSpace: 'nowrap',
  boxSizing: 'border-box',
  ...(open && {
    ...openedMixin(theme),
    '& .MuiDrawer-paper': {
      ...openedMixin(theme),
      position: 'absolute',
      inset: 0,
      borderRight: `1px solid ${theme.palette.divider}`,
      backgroundColor: theme.palette.background.paper,
    },
  }),
  ...(!open && {
    ...closedMixin(theme),
    '& .MuiDrawer-paper': {
      ...closedMixin(theme),
      position: 'absolute',
      inset: 0,
      borderRight: `1px solid ${theme.palette.divider}`,
      backgroundColor: theme.palette.background.paper,
    },
  }),
}));

const navigationItems = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    icon: <DashboardOutlinedIcon />,
    isRoute: true,
  },
  {
    href: '#applications',
    label: 'Applications',
    icon: <WorkOutlineOutlinedIcon />,
    isRoute: false,
  },
  {
    href: '#reminders',
    label: 'Reminders',
    icon: <NotificationsNoneOutlinedIcon />,
    isRoute: false,
  },
] as const;

const Sidebar = () => {
  const { isAuthenticated } = useAuth();
  const theme = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  if (!isAuthenticated) {
    return null;
  }

  const handleDrawerToggle = () => {
    setIsOpen((previousState) => !previousState);
  };

  const collapseDrawer = () => {
    setIsOpen(false);
  };

  return (
    <Box
      data-testid="sidebar-shell"
      sx={(currentTheme) => ({
        position: 'relative',
        flexShrink: 0,
        whiteSpace: 'nowrap',
        width: isOpen ? drawerWidth : `calc(${currentTheme.spacing(7)} + 1px)`,
        [currentTheme.breakpoints.up('sm')]: {
          width: isOpen ? drawerWidth : `calc(${currentTheme.spacing(8)} + 1px)`,
        },
      })}
    >
      <MiniDrawer variant="permanent" open={isOpen}>
        <Box component="nav" aria-label="Sidebar navigation" sx={{ height: '100%' }}>
          <DrawerHeader>
            <IconButton
              aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              aria-expanded={isOpen}
              onClick={handleDrawerToggle}
            >
              {isOpen ? (
                theme.direction === 'rtl' ? (
                  <ChevronRightIcon />
                ) : (
                  <ChevronLeftIcon />
                )
              ) : (
                <MenuOutlinedIcon />
              )}
            </IconButton>
          </DrawerHeader>
          <Divider />
          <List>
            {navigationItems.map((item) => {
              const buttonProps = item.isRoute
                ? { component: RouterLink, to: item.href }
                : { component: 'a' as const, href: item.href };

              return (
                <ListItem key={item.label} disablePadding sx={{ display: 'block' }}>
                  <ListItemButton
                    {...buttonProps}
                    onClick={collapseDrawer}
                    sx={{
                      minHeight: 48,
                      justifyContent: isOpen ? 'initial' : 'center',
                      px: 2.5,
                    }}
                  >
                    <ListItemIcon
                      sx={{
                        minWidth: 0,
                        mr: isOpen ? 3 : 'auto',
                        justifyContent: 'center',
                      }}
                    >
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText primary={item.label} sx={{ opacity: isOpen ? 1 : 0 }} />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        </Box>
      </MiniDrawer>
    </Box>
  );
};

export default Sidebar;
