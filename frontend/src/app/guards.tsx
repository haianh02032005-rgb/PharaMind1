import React, { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading, user, hydrate } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && !user) {
      void hydrate();
    }
  }, [isAuthenticated, user, hydrate]);

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--pm-text-secondary)",
        }}
      >
        Đang kết nối PharmaMind AI...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};

