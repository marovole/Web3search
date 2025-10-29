import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const textareaVariants = cva(
  "flex w-full rounded-md border bg-background text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200 resize-none",
  {
    variants: {
      variant: {
        default: "border-input hover:border-primary/50 focus-visible:border-primary",
        floating: "border-transparent border-b-2 rounded-none px-0 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-0",
        error: "border-destructive hover:border-destructive/80 focus-visible:ring-destructive",
        success: "border-green-500 hover:border-green-600 focus-visible:ring-green-500",
      },
      size: {
        default: "px-3 py-2 min-h-[44px]",
        sm: "px-3 py-1 min-h-[38px]",
        lg: "px-4 py-3 min-h-[50px]",
        floating: "px-0 pt-6 min-h-[56px]",
      },
      inputState: {
        default: "",
        loading: "pr-10",
        error: "pr-10",
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      inputState: "default",
    },
  }
)

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement>,
    VariantProps<typeof textareaVariants> {
  label?: string
  error?: string
  success?: string
  loading?: boolean
  helperText?: string
  autoResize?: boolean
  maxHeight?: number
}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({
    className,
    variant,
    size,
    inputState,
    label,
    error,
    success,
    loading,
    helperText,
    value,
    autoResize = true,
    maxHeight = 200,
    ...props
  }, ref) => {
    const [focused, setFocused] = React.useState(false)
    const textareaRef = React.useRef<HTMLTextAreaElement>(null)
    const hasValue = value !== undefined && value !== ""

    // Determine actual variant based on state
    const actualVariant = error ? "error" : success ? "success" : variant
    const actualInputState = loading ? "loading" : error ? "error" : inputState

    const isFloating = variant === "floating"
    const showFloatingLabel = isFloating && (focused || hasValue)

    // Auto-resize functionality
    const adjustHeight = React.useCallback(() => {
      if (autoResize && textareaRef.current) {
        const textarea = textareaRef.current
        textarea.style.height = 'auto'
        const newHeight = Math.min(textarea.scrollHeight, maxHeight)
        textarea.style.height = `${newHeight}px`
      }
    }, [autoResize, maxHeight])

    // Combine refs
    React.useImperativeHandle(ref, () => textareaRef.current!)
    React.useEffect(adjustHeight, [value, adjustHeight])

    const handleFocus = (e: React.FocusEvent<HTMLTextAreaElement>) => {
      setFocused(true)
      props.onFocus?.(e)
    }

    const handleBlur = (e: React.FocusEvent<HTMLTextAreaElement>) => {
      setFocused(false)
      props.onBlur?.(e)
    }

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      if (autoResize) {
        adjustHeight()
      }
      props.onChange?.(e)
    }

    return (
      <div className="relative w-full">
        {/* Floating Label */}
        {isFloating && label && (
          <label
            className={cn(
              "absolute left-0 top-0 z-10 origin-left transition-all duration-200 pointer-events-none",
              showFloatingLabel
                ? "translate-y-1 scale-75 text-muted-foreground"
                : "translate-y-3 scale-100 text-foreground"
            )}
          >
            {label}
          </label>
        )}

        {/* Standard Label */}
        {!isFloating && label && (
          <label className="mb-2 block text-sm font-medium text-foreground">
            {label}
          </label>
        )}

        {/* Input Container */}
        <div className="relative">
          <textarea
            {...props}
            value={value}
            ref={textareaRef}
            className={cn(
              textareaVariants({ variant: actualVariant, size, inputState: actualInputState }),
              className
            )}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onChange={handleChange}
            style={{
              ...props.style,
              ...(autoResize && { overflowY: 'hidden' })
            }}
          />

          {/* Loading Indicator */}
          {loading && (
            <div className="absolute right-3 top-3">
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
            </div>
          )}

          {/* Error Icon */}
          {error && !loading && (
            <div className="absolute right-3 top-3 text-destructive">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          )}

          {/* Success Icon */}
          {success && !loading && !error && (
            <div className="absolute right-3 top-3 text-green-500">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          )}
        </div>

        {/* Helper Text */}
        {(helperText || error || success) && (
          <p className={cn(
            "mt-2 text-xs",
            error ? "text-destructive" :
            success ? "text-green-600" :
            "text-muted-foreground"
          )}>
            {error || success || helperText}
          </p>
        )}
      </div>
    )
  }
)
Textarea.displayName = "Textarea"

export { Textarea, textareaVariants }