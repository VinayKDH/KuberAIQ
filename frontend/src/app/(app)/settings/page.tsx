"use client";

import { Building2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { getStoredUser } from "@/lib/auth";

export default function SettingsPage() {
  const user = getStoredUser();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Manage your company and account preferences</p>
      </div>

      <Tabs defaultValue="company">
        <TabsList>
          <TabsTrigger value="company">Company</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
        </TabsList>

        <TabsContent value="company" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-muted-foreground" />
                <CardTitle>Company Information</CardTitle>
              </div>
              <CardDescription>
                GST billing details used on invoices and reports
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="company-name">Company Name</Label>
                  <Input id="company-name" placeholder="ABC Traders Pvt Ltd" disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="gstin">GSTIN</Label>
                  <Input id="gstin" placeholder="27ABCDE1234F1Z5" disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="state">State Code</Label>
                  <Input id="state" placeholder="27" disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input id="phone" placeholder="+91 98765 43210" disabled />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="address">Billing Address</Label>
                <Textarea
                  id="address"
                  placeholder="MIDC Industrial Area, Pune, Maharashtra 411019"
                  disabled
                  rows={3}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Company settings will be editable once connected to the backend.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="account" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Account</CardTitle>
              <CardDescription>Your profile and role</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input value={user?.full_name ?? ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input value={user?.email ?? ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Input value={user?.role ?? ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label>Company ID</Label>
                  <Input value={user?.company_id ?? ""} disabled className="font-mono text-xs" />
                </div>
              </div>
              <Separator />
              <p className="text-sm text-muted-foreground">
                Authentication is managed via Microsoft Entra ID in production.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
