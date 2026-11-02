import React, { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "./guards";
import { AppShell } from "../components/navigation/AppShell";

const LoginPage = lazy(() => import("../pages/auth/LoginPage").then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import("../pages/auth/RegisterPage").then((m) => ({ default: m.RegisterPage })));
const DashboardPage = lazy(() => import("../pages/dashboard/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const FamilyPage = lazy(() => import("../pages/family/FamilyPage").then((m) => ({ default: m.FamilyPage })));
const MemberDetailPage = lazy(() => import("../pages/members/MemberDetailPage").then((m) => ({ default: m.MemberDetailPage })));
const MedicationsPage = lazy(() => import("../pages/medications/MedicationsPage").then((m) => ({ default: m.MedicationsPage })));
const PrescriptionsPage = lazy(() => import("../pages/prescriptions/PrescriptionsPage").then((m) => ({ default: m.PrescriptionsPage })));
const SchedulesPage = lazy(() => import("../pages/schedules/SchedulesPage").then((m) => ({ default: m.SchedulesPage })));
const CabinetPage = lazy(() => import("../pages/cabinet/CabinetPage").then((m) => ({ default: m.CabinetPage })));
const DigitalTwinPage = lazy(() => import("../pages/digital-twin/DigitalTwinPage").then((m) => ({ default: m.DigitalTwinPage })));
const AiPharmacistPage = lazy(() => import("../pages/ai/AiPharmacistPage").then((m) => ({ default: m.AiPharmacistPage })));
const SettingsPage = lazy(() => import("../pages/settings/SettingsPage").then((m) => ({ default: m.SettingsPage })));
const ImportPrescriptionPage = lazy(() => import("../pages/import-prescription/ImportPrescriptionPage").then((m) => ({ default: m.ImportPrescriptionPage })));

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<div role="status" style={{ padding: 24 }}>Đang tải PharmaMind…</div>}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/family" element={<FamilyPage />} />
            <Route path="/members/:memberId" element={<MemberDetailPage />} />
            <Route path="/medications" element={<MedicationsPage />} />
            <Route path="/prescriptions" element={<PrescriptionsPage />} />
            <Route path="/import-prescription" element={<ImportPrescriptionPage />} />
            <Route path="/schedules" element={<SchedulesPage />} />
            <Route path="/cabinet" element={<CabinetPage />} />
            <Route path="/digital-twin" element={<DigitalTwinPage />} />
            <Route path="/ai" element={<AiPharmacistPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

