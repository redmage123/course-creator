/**
 * Register Page Barrel Export
 *
 * Re-exports RegistrationPage component for cleaner imports.
 * This allows App.tsx to import from ./features/auth/Register
 * instead of the full path ./features/auth/pages/RegistrationPage/RegistrationPage
 */

export { RegistrationPage as RegisterPage } from './pages/RegistrationPage';
