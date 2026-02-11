import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { MessageSquare, Plus } from "lucide-react";

export default function Chat() {
  return (
    <div className="flex h-full flex-col">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Chat</h1>
          <p className="text-muted-foreground">
            Ask questions and get AI-powered answers
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          New Conversation
        </Button>
      </div>

      <Card className="flex flex-1 items-center justify-center">
        <CardContent className="text-center">
          <MessageSquare className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
          <CardTitle className="mb-2">No conversation selected</CardTitle>
          <CardDescription>
            Start a new conversation or select an existing one to begin chatting.
          </CardDescription>
        </CardContent>
      </Card>
    </div>
  );
}
