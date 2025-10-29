import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const inputVariants = cva(
  "flex w-full rounded-md border bg-background text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200",
  {
    variants: {
      variant: {
        default: "border-input hover:border-primary/50 focus-visible:border-primary",
        floating: "border-transparent border-b-2 rounded-none px-0 h-12 hover:border-primary/50 focus-visible:border-primary focus-visible:ring-0",
        error: "border-destructive hover:border-destructive/80 focus-visible:ring-destructive",
        success: "border-green-500 hover:border-green-600 focus-visible:ring-green-500",
      },
      size: {
        default: "h-10 px-3 py-2",
        sm: "h-9 px-3 py-1",
        lg: "h-11 px-4 py-3",
        floating: "h-12 px-0 pt-6",
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

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  label?: string
  error?: string
  success?: string
  loading?: boolean
  helperText?: string
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({
    className,
    type,
    variant,
    size,
    inputState,
    label,
    error,
    success,
    loading,
    helperText,
    value,
    ...props
  }, ref) => {
    const [focused, setFocused] = React.useState(false)
    const hasValue = value !== undefined && value !== ""

    // Determine actual variant based on state
    const actualVariant = error ? "error" : success ? "success" : variant
    const actualInputState = loading ? "loading" : error ? "error" : inputState

    const isFloating = variant === "floating"
    const showFloatingLabel = isFloating && (focused || hasValue)

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
          <input
            type={type}
            className={cn(
              inputVariants({ variant: actualVariant, size, inputState: actualInputState }),
              // Touch-friendly sizing for mobile
              "min-h-[44px] md:min-h-0",
              className
            )}
            ref={ref}
            value={value}
            onFocus={(e) => {
              setFocused(true)
              props.onFocus?.(e)
            }}
            onBlur={(e) => {
              setFocused(false)
              props.onBlur?.(e)
            }}
            {...props}
          />

          {/* Loading Indicator */}
          {loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
            </div>
          )}

          {/* Error Icon */}
          {error && !loading && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-destructive">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          )}

          {/* Success Icon */}
          {success && !loading && !error && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-green-500">
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
Input.displayName = "Input"

export { Input, inputVariants }