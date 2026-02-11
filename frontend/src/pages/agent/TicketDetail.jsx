import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function TicketDetail() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Tickets</h1>
        <p className="text-muted-foreground">
          View and manage your assigned support tickets
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Tickets</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No tickets available. When customers escalate conversations, they will appear here.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
