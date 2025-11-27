import {
  BrowserRouter as Router,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import Footer from "./components/Footer";
import Hero from "./components/Hero";
import Info from "./components/Info";
import Navbar from "./components/Navbar";
import IngredientUploadPage from "./pages/Ingrident";
import FavoritesPage from "./pages/Favorites";
import CollectionsPage from "./pages/Collections";
import LoginPage from "./pages/Login";
import SignupPage from "./pages/Signup";
import EditProfilePage from "./pages/EditProfile";
import UserPreferences from "./components/UserPreference";
import About from "./pages/About";
import Blog from "./pages/Blog";
import PrivacyPolicy from "./pages/PrivacyPolicy";
import StaticRecipes from "./pages/StaticRecipes";
import BrowseRecipes from "./pages/PreviousRecepies";

// Layout wrapper to handle conditional Footer
const Layout = () => {
  const location = useLocation();

  return (
    <div>
      <Navbar />
      <Routes>
        {/* Public Routes */}
        
        {/* Home Page - Public */}
        <Route
          path="/"
          element={
            <>
              <Hero />
              <Info />
            </>
          }
        />

        {/* Auth Routes - Redirect to home if already logged in */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Static Recipes - Public (browsing allowed without login) */}
        <Route path="/recipes" element={<StaticRecipes />} />

        {/* Protected Routes - Require Authentication */}
        <Route path="/browse" element={<BrowseRecipes />} />

        {/* Ingredient Upload Page */}
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <IngredientUploadPage onNavigate={() => {}} />
            </ProtectedRoute>
          }
        />

        {/* Favorites Page */}
        <Route 
          path="/favorites" 
          element={
            <ProtectedRoute>
              <FavoritesPage />
            </ProtectedRoute>
          } 
        />

        {/* Collections Page */}
        <Route 
          path="/collections" 
          element={
            <ProtectedRoute>
              <CollectionsPage />
            </ProtectedRoute>
          } 
        />

        {/* Profile Management */}
        <Route 
          path="/edit-profile" 
          element={
            <ProtectedRoute>
              <EditProfilePage />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/preferences" 
          element={
            <ProtectedRoute>
              <UserPreferences />
            </ProtectedRoute>
          } 
        />

        {/* Public Info Pages */}
        <Route path="/about" element={<About />} />
        <Route path="/blog" element={<Blog />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />

        {/* 404 Page */}
        <Route path="*" element={<div className="p-10">Page Not Found</div>} />
      </Routes>

      {/* Hide footer only on /upload */}
      {location.pathname !== "/upload" && <Footer />}
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <AuthProvider>
        <Layout />
      </AuthProvider>
    </Router>
  );
};

export default App;