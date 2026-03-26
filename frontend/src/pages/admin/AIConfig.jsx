import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { getAiConfig, updateAiConfig } from "@/services/aiConfigApi";

export default function AIConfig() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["ai-config"],
    queryFn: getAiConfig,
  });

  const [systemTemplateExtension, setSystemTemplateExtension] = useState("");
  const [noEscalateOutOfScope, setNoEscalateOutOfScope] = useState(true);

  useEffect(() => {
    if (!data) return;
    setSystemTemplateExtension(data.system_template_extension || "");
    setNoEscalateOutOfScope(Boolean(data.no_escalate_out_of_scope));
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: updateAiConfig,
    onSuccess: () => {
      toast.success("AI configuration saved");
      refetch();
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || "Failed to save AI configuration");
    },
  });

  const handleSave = () => {
    saveMutation.mutate({
      system_template_extension: systemTemplateExtension,
      no_escalate_out_of_scope: noEscalateOutOfScope,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">AI Configuration</h1>
        <p className="text-muted-foreground">
          Customize assistant behavior for your organization.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Template</CardTitle>
          <CardDescription>
            Define exactly how the assistant should behave for your organization.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Label htmlFor="system-template-extension">Template text</Label>
          <Textarea
            id="system-template-extension"
            className="mt-2 min-h-40"
            placeholder="Example: You are the support assistant for Acme Logistics. Behave like a real support agent, be concise, and stay within company operations and policies..."
            value={systemTemplateExtension}
            onChange={(e) => setSystemTemplateExtension(e.target.value)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Out-of-Scope Handling</CardTitle>
          <CardDescription>
            Configure what users see for questions outside company operations.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3 rounded-md border p-3">
            <Input
              id="no-escalate-out-of-scope"
              type="checkbox"
              checked={noEscalateOutOfScope}
              onChange={(e) => setNoEscalateOutOfScope(e.target.checked)}
              className="h-4 w-4"
            />
            <div>
              <Label htmlFor="no-escalate-out-of-scope" className="cursor-pointer">
                Do not escalate out-of-scope questions
              </Label>
              <p className="text-xs text-muted-foreground mt-1">
                When enabled, outside-company questions return your out-of-scope response without creating a support ticket.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isLoading || saveMutation.isPending}>
          {saveMutation.isPending ? "Saving..." : "Save Configuration"}
        </Button>
      </div>
    </div>
  );
}
