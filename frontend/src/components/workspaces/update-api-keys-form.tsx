// @ts-nocheck
"use client";
import React, { useEffect, useRef, useState } from "react";
import { AuthActions } from "@/lib/auth";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { PasswordInput } from "../ui/password-input";
import { LoaderButton } from "../ui/LoadingSpinner";
import { Avatar } from "@radix-ui/react-avatar";
import WorkspaceIcon from "@/components/workspaces/workspace-icon";
import { Upload } from "lucide-react";
import { fetcher } from "@/app/fetcher";
import { useSWRConfig } from "swr";
import useSession from "@/app/hooks/use-session";

const FormSchema = z.object({
  openaiApiKey: z.string().nullable(),
  anthropicApiKey: z.string().nullable(),
});

type FormData = z.infer<typeof FormSchema>;

const UpdateApiKeysForm = ({ workspace, enabled }: any) => {
  const [formRespError, setFormRespError] = useState<string | null>(null);
  const [inUseProvider, setInUseProvider] = useState<string | null>(workspace.provider_in_use || null);

  const [isLoading, setIsLoading] = useState<boolean>(false);

  const { mutate } = useSWRConfig();

  const form = useForm<z.infer<typeof FormSchema>>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      openaiApiKey: workspace.openai_api_key,
      anthropicApiKey: workspace.anthropic_api_key,
      providerInUse: workspace.provider_in_use,
    },
  });

  useEffect(() => {
    form.setValue("openaiApiKey", workspace.openai_api_key);
    form.setValue("anthropicApiKey", workspace.anthropic_api_key);
    setInUseProvider(workspace.provider_in_use);
  }, [workspace]);

  const onSubmit = async (data: any) => {
    const openaiApiKey = data.openaiApiKey?.trim();
    const anthropicApiKey = data.anthropicApiKey?.trim();
    setIsLoading(true);
    setFormRespError(null);
    try {
      const resp = await fetcher("/workspaces/" + workspace.id + "/", {
        method: "PUT",
        body: {
          openai_api_key: openaiApiKey,
          anthropic_api_key: anthropicApiKey,
        },
      });
      mutate("/auth/users/me/");
      setIsLoading(false);
    } catch (err: any) {
      setFormRespError(err.json.detail);
    }
  };

  const handleMakeInUse = async (provider: string) => {
      try {
          const newProvider = inUseProvider === provider ? "" : provider;
          const resp = await fetcher("/workspaces/" + workspace.id + "/", {
              method: "PUT",
              body: {
                  provider_in_use: newProvider,
                },
            });
        mutate("/auth/users/me/");
        setInUseProvider(newProvider);
        setIsLoading(false);
      } catch (err: any) {
        setFormRespError(err.json.detail);
      }
  };

  const openaiApiKey = form.watch("openaiApiKey");
  const anthropicApiKey = form.watch("anthropicApiKey");

  return (
    <div className="space-y-4">
      {formRespError && (
        <CardDescription className="mb-2 py-2 text-red-500 font-medium">
          {formRespError}
        </CardDescription>
      )}
      <div className="grid gap-8">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <FormField
              control={form.control}
              name="openaiApiKey"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>OpenAI</FormLabel>
                  <div className="flex items-center space-x-2">
                    <FormControl>
                      <Input
                        disabled={isLoading || !enabled}
                        {...field}
                      />
                    </FormControl>
                    <Button
                      type="button"
                      onClick={() => handleMakeInUse('openai')}
                      disabled={isLoading || !enabled}
                      variant={inUseProvider === 'openai' ? 'default' : 'outline'}
                    >
                      {inUseProvider === 'openai' ? 'In Use' : 'Make in Use'}
                    </Button>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="anthropicApiKey"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Anthropic</FormLabel>
                  <div className="flex items-center space-x-2">
                    <FormControl>
                      <Input
                        disabled={isLoading || !enabled}
                        {...field}
                      />
                    </FormControl>
                    <Button
                      type="button"
                      onClick={() => handleMakeInUse('anthropic')}
                      disabled={isLoading || !enabled}
                      variant={inUseProvider === 'anthropic' ? 'default' : 'outline'}
                    >
                      {inUseProvider === 'anthropic' ? 'In Use' : 'Make in Use'}
                    </Button>
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />

            {enabled && (
              <LoaderButton
                isLoading={isLoading}
                className="float-right"
                type="submit"
              >
                Save
              </LoaderButton>
            )}
          </form>
        </Form>
      </div>
    </div>
  );
};

export default UpdateApiKeysForm;
